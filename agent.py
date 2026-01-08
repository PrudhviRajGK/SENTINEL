import os
import re
import requests
import json
import base64
import io
from PIL import Image
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from dotenv import load_dotenv
from checkDMARC import *
from serperSearch import *
from educationalModuleRAG import *
from agent_orchestrator import AgentOrchestrator, ThreatSignal, InputType
from voice_analysis import VoiceScamAnalyzer
from cyber_news import CyberNewsIntelligence
from deepfake_detection import DeepfakeDetector

# Load environment variables from .env file
load_dotenv()

requests.packages.urllib3.disable_warnings()
SERPER_API_KEY=os.environ.get('SERPER_API_KEY')

openai_api_key = os.environ.get('OPENAI_API_KEY')
url_hause_key = os.environ.get('URL_HAUSE_KEY')

if not SERPER_API_KEY or not openai_api_key:
    raise ValueError("API keys not found. Please set SERPER_API_KEY and OPENAI_API_KEY environment variables.")


class CybersecurityAgent:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.vt_api_key = os.environ.get('VT_API_KEY')

        if not self.openai_api_key or not self.vt_api_key or not SERPER_API_KEY:
            raise ValueError("API keys not found. Please set OPENAI_API_KEY and VT_API_KEY and SERPER_API_KEY environment variables.")

        self.llm = ChatOpenAI(model="gpt-4o", openai_api_key=self.openai_api_key, temperature=0)
        self.vision_llm = ChatOpenAI(model="gpt-4o", openai_api_key=self.openai_api_key, temperature=0)
        
        # Initialize voice analyzer
        self.voice_analyzer = VoiceScamAnalyzer()
        
        # Initialize cyber news intelligence
        self.news_intel = CyberNewsIntelligence()
        self.cached_news = []  # Cache news for session
        
        # Initialize deepfake detector
        self.deepfake_detector = DeepfakeDetector()
        
        # Initialize orchestrator with tool wrappers
        self.orchestrator = AgentOrchestrator(
            llm=self.llm,
            tools_dict=self._create_tool_wrappers()
        )
        
        self.setup_agent()
    
    def _create_tool_wrappers(self):
        """
        Create tool wrappers that return ThreatSignal objects
        This allows the orchestrator to weigh signals intelligently
        """
        return {
            'virustotal': self._virustotal_wrapper,
            'urlhaus': self._urlhaus_wrapper,
            'phone_search': self._phone_wrapper,
            'llm_analysis': self._llm_wrapper,
            'voice_analysis': self._voice_wrapper,
            'deepfake_detection': self._deepfake_wrapper,
            'news_correlation': self._news_wrapper
        }
    
    def _virustotal_wrapper(self, url: str) -> ThreatSignal:
        """Wrapper for VirusTotal that returns structured signal"""
        try:
            vt_data = self.queryVirusTotal(url)
            if vt_data.startswith("Error:"):
                return None
            
            # Parse VT response
            vt_json = json.loads(vt_data)
            stats = vt_json.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
            
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            harmless = stats.get('harmless', 0)
            total = malicious + suspicious + harmless
            
            # Calculate score (0-100)
            if total > 0:
                score = ((malicious * 2 + suspicious) / total) * 100
            else:
                score = 0
            
            # Confidence based on number of engines
            confidence = min(70 + (total / 10), 95)
            
            evidence = f"{malicious}/{total} engines flagged as malicious"
            
            return ThreatSignal(
                source='VirusTotal',
                score=score,
                confidence=confidence,
                evidence=evidence,
                raw_data=stats
            )
        except Exception as e:
            print(f"VirusTotal wrapper error: {e}")
            return None
    
    def _urlhaus_wrapper(self, url: str) -> ThreatSignal:
        """Wrapper for URLhaus that returns structured signal"""
        try:
            urlhaus_data = self.queryUrlHause(url)
            
            if urlhaus_data == "No results":
                return ThreatSignal(
                    source='URLhaus',
                    score=0,
                    confidence=80,
                    evidence="Not listed in URLhaus database (positive indicator)",
                    raw_data=None
                )
            elif "Something went wrong" in urlhaus_data:
                return None
            else:
                # URL is in URLhaus - high risk
                return ThreatSignal(
                    source='URLhaus',
                    score=90,
                    confidence=95,
                    evidence="Listed in URLhaus malware database",
                    raw_data=json.loads(urlhaus_data) if urlhaus_data else None
                )
        except Exception as e:
            print(f"URLhaus wrapper error: {e}")
            return None
    
    def _phone_wrapper(self, phone: str) -> ThreatSignal:
        """Wrapper for phone analysis that returns structured signal"""
        try:
            result = self.analyze_phone(phone)
            
            # Use LLM to score the phone analysis
            score_prompt = f"""Based on this phone number analysis, provide a risk score (0-100):
            
Analysis: {result}

Consider:
- Mentions of scam/fraud: high score
- Negative reviews: medium-high score  
- No information: low score
- Positive reviews: very low score

Respond with just a number 0-100:"""
            
            score_response = self.llm.invoke(score_prompt)
            score_text = score_response.content if hasattr(score_response, 'content') else str(score_response)
            
            try:
                score = float(re.search(r'\d+', score_text).group())
            except:
                score = 50  # Default if parsing fails
            
            return ThreatSignal(
                source='Phone Search',
                score=score,
                confidence=60,  # Search results have moderate confidence
                evidence=result[:200],  # Truncate
                raw_data=None
            )
        except Exception as e:
            print(f"Phone wrapper error: {e}")
            return None
    
    def _llm_wrapper(self, text: str) -> ThreatSignal:
        """Wrapper for LLM analysis that returns structured signal"""
        try:
            analysis = self.analyze_message(text)
            
            # Extract risk indicators from LLM response
            analysis_lower = analysis.lower()
            
            risk_keywords = {
                'high': ['phishing', 'scam', 'malicious', 'dangerous', 'fraud'],
                'medium': ['suspicious', 'concerning', 'caution', 'warning'],
                'low': ['legitimate', 'safe', 'normal', 'benign']
            }
            
            score = 30  # Default
            for level, keywords in risk_keywords.items():
                if any(kw in analysis_lower for kw in keywords):
                    if level == 'high':
                        score = 75
                    elif level == 'medium':
                        score = 50
                    else:
                        score = 15
                    break
            
            return ThreatSignal(
                source='LLM Analysis',
                score=score,
                confidence=70,
                evidence=analysis[:200],
                raw_data=None
            )
        except Exception as e:
            print(f"LLM wrapper error: {e}")
            return None
    
    def _voice_wrapper(self, audio_path: str) -> ThreatSignal:
        """Wrapper for voice analysis that returns structured signal"""
        try:
            result = self.voice_analyzer.analyze_call(audio_path)
            
            # Map risk level to score
            risk_map = {
                'high': 85,
                'medium': 60,
                'low': 30,
                'minimal': 10
            }
            
            score = risk_map.get(result['risk_level'], 50)
            
            return ThreatSignal(
                source='Voice Analysis',
                score=score,
                confidence=result['confidence'],
                evidence=result['verdict'],
                raw_data=result
            )
        except Exception as e:
            print(f"Voice wrapper error: {e}")
            return None
    
    def _deepfake_wrapper(self, media_path: str) -> ThreatSignal:
        """Wrapper for deepfake detection"""
        try:
            # Determine if image or video
            ext = media_path.lower().split('.')[-1]
            
            if ext in ['mp4', 'avi', 'mov', 'mkv']:
                result = self.deepfake_detector.analyze_video(media_path)
            else:
                result = self.deepfake_detector.analyze_image(media_path)
            
            if 'error' in result:
                return None
            
            # Convert authenticity to threat score
            # Authentic = low threat, Manipulated = high threat
            if result['authentic'] is True:
                score = 10  # Authentic = low threat
            elif result['authentic'] is False:
                score = 85  # Manipulated = high threat
            else:
                score = 50  # Uncertain
            
            return ThreatSignal(
                source='Deepfake Detection',
                score=score,
                confidence=result['confidence'],
                evidence=result['verdict'],
                raw_data=result
            )
        except Exception as e:
            print(f"Deepfake wrapper error: {e}")
            return None
    
    def _news_wrapper(self, input_text: str) -> ThreatSignal:
        """Wrapper for news correlation"""
        try:
            # Fetch news if not cached
            if not self.cached_news:
                self.cached_news = self.news_intel.fetch_recent_threats(days_back=7, max_results=20)
            
            # Check for correlation
            correlation = self.news_intel.correlate_with_analysis(input_text, self.cached_news)
            
            if correlation and correlation.get('related'):
                # Related to recent threat news = higher risk
                return ThreatSignal(
                    source='Threat Intelligence',
                    score=65,
                    confidence=70,
                    evidence=correlation['context'],
                    raw_data=correlation
                )
            else:
                # No correlation = neutral signal
                return ThreatSignal(
                    source='Threat Intelligence',
                    score=30,
                    confidence=50,
                    evidence='No correlation with recent threat reports',
                    raw_data=None
                )
        except Exception as e:
            print(f"News wrapper error: {e}")
            return None


    def queryUrlHause(self, url):
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        if not url_hause_key:
            return "Error: URL_HAUSE_KEY environment variable not set."
        
        data = {'url': url}
        headers = {
            'Auth-Key': url_hause_key
        }
        
        response = requests.post('https://urlhaus-api.abuse.ch/v1/url/', headers=headers, data=data)
        json_response = response.json()
        
        if json_response['query_status'] == 'ok':
            return json.dumps(json_response, indent=4, sort_keys=False)
        elif json_response['query_status'] == 'no_results':
            url = 'http://' + url[8:]
            response = requests.post('https://urlhaus-api.abuse.ch/v1/url/', headers=headers, data={'url': url})
            json_response = response.json()
            if json_response['query_status'] == 'ok':
                return json.dumps(json_response, indent=4, sort_keys=False)
            elif json_response['query_status'] == 'no_results':
                return "No results"
            else:
                return "Something went wrong"
        else:
            return "Something went wrong"


    def queryVirusTotal(self, url):
        VTapiEndpoint = "https://www.virustotal.com/api/v3/urls"
        payload = f'url={url}'
        headers = {
            'x-apikey': self.vt_api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(VTapiEndpoint, headers=headers, data=payload)
        try:
            VTurlID = response.json()["data"]["links"]["self"]
            response = requests.request("GET", VTurlID, headers=headers)
            return response.text
        except KeyError:
            return "Error: Invalid response data from VirusTotal API"

    def analyze_domain(self, url):
        vt_data = self.queryVirusTotal(url)
        if vt_data.startswith("Error:"):
            return vt_data
        urlhaus_data = self.queryUrlHause(url)

        template = """
        Analyze the following JSON data from two domain scan sources:
        VirusTotal scan: {JSON_DATA_Virus_Total}
        URLhaus scan: {JSON_DATA_URL_HOUSE}

        Based on the analysis, generate a brief assessment following these rules:
        1. Start with "Based on related databases, domain identified as [malicious/suspicious/secure]"
        2. Use "malicious" if VirusTotal malicious count > 0 or URLhaus query_status is "ok"
        3. Use "suspicious" if VirusTotal suspicious count > 0 or undetected count is high
        4. Use "secure" if VirusTotal harmless count is high and malicious/suspicious counts are 0, and URLhaus query_status is "no_results"
        5. Highlight the URL status as online/offline/unknown from URLhaus data
        6. Check the blacklists key in URLhaus data and highlight if the domain is identified as a spammer domain, phishing domain, botnet C&C domain, compromised website, or not listed
        7. Provide a short summary of up to 10 words
        8. Add a brief description if needed, focusing on key findings

        Output the assessment in a concise paragraph.
        """
        prompt = PromptTemplate(template=template, input_variables=["JSON_DATA_Virus_Total", "JSON_DATA_URL_HOUSE"])
        chain = prompt | self.llm | RunnableLambda(lambda x: x.content)
        return chain.invoke({"JSON_DATA_Virus_Total": vt_data, "JSON_DATA_URL_HOUSE": urlhaus_data})

    def describe_image(self, image_path):
        with Image.open(image_path) as img:
            img = img.convert('RGB')
            img_data = io.BytesIO()
            img.save(img_data, format='JPEG')
            img_data.seek(0)
            image_data = base64.b64encode(img_data.read()).decode('utf-8')

        model = ChatOpenAI(model="gpt-4o", openai_api_key=self.openai_api_key, temperature=0)
        IMAGE_DESCRIPTION_PROMPT = """
        Analyze the following image in detail:

        1. Describe the overall layout and visual elements of the image.

        2. Extract and list ALL text visible in the image, exactly as it appears. Do not paraphrase or summarize. Include:
           - Headings
           - Body text
           - Labels
           - Buttons
           - Any other visible text

        3. Identify and list any of the following types of information, if present:
           - Email addresses
           - Phone numbers
           - Web domains
           - IP addresses
           - Social media handles
           - Names of people or organizations
           - Dates
           - Locations

        4. Note any logos, icons, or distinctive visual elements.

        5. Describe any charts, graphs, or data visualizations, if present.

        6. Mention any notable color schemes or design elements.

        7. If the image appears to be a screenshot of a specific type of content (e.g., email, social media post, web page), identify it.

        Please be as thorough and precise as possible in your analysis, ensuring that all text is captured exactly as it appears in the image.
        """
        message = HumanMessage(
            content=[
                {"type": "text", "text": IMAGE_DESCRIPTION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    },
                },
            ],
        )
        response = model.invoke([message])
        return response.content

    def agentic_analyze(self, user_input: str, input_type_hint: str = None, language: str = 'en'):
        """
        NEW: Agentic analysis using orchestrator with multilingual support
        This is the main entry point for intelligent, reasoned analysis
        
        Args:
            user_input: The content to analyze
            input_type_hint: Optional hint about input type (voice, video, image_deepfake)
            language: Language for response ('en' or 'hi')
        """
        # Handle special input types
        if input_type_hint == 'voice':
            # user_input should be file path
            try:
                voice_result = self.voice_analyzer.analyze_call(user_input, language=language)
                return {
                    'type': 'voice',
                    'transcript': voice_result['transcript'],
                    'risk_level': voice_result['risk_level'],
                    'confidence': voice_result['confidence'],
                    'indicators': voice_result['scam_indicators'],
                    'reasoning': voice_result['reasoning'],
                    'verdict': voice_result['verdict'],
                    'recommendations': self._get_voice_recommendations(voice_result['risk_level'], language)
                }
            except Exception as e:
                return {
                    'error': f'Voice analysis failed: {str(e)}'
                }
        
        if input_type_hint == 'video':
            # Video deepfake analysis
            try:
                video_result = self.deepfake_detector.analyze_video(user_input)
                
                if 'error' in video_result:
                    return {'error': video_result['error']}
                
                # Determine risk level from authenticity
                if video_result['authentic'] is True:
                    risk_level = 'minimal'
                elif video_result['authentic'] is False:
                    risk_level = 'high'
                else:
                    risk_level = 'medium'
                
                return {
                    'type': 'video',
                    'risk_level': risk_level,
                    'confidence': video_result['confidence'],
                    'verdict': self._localize_deepfake_verdict(video_result['verdict'], language),
                    'reasoning': video_result['reasoning'],
                    'frames_analyzed': video_result.get('frames_analyzed', 0),
                    'limitations': video_result.get('limitations', ''),
                    'recommendations': self._get_deepfake_recommendations(risk_level, language)
                }
            except Exception as e:
                return {
                    'error': f'Video analysis failed: {str(e)}'
                }
        
        if input_type_hint == 'image_deepfake':
            # Image deepfake analysis
            try:
                image_result = self.deepfake_detector.analyze_image(user_input)
                
                if 'error' in image_result:
                    return {'error': image_result['error']}
                
                # Determine risk level from authenticity
                if image_result['authentic'] is True:
                    risk_level = 'minimal'
                elif image_result['authentic'] is False:
                    risk_level = 'high'
                else:
                    risk_level = 'medium'
                
                return {
                    'type': 'image',
                    'risk_level': risk_level,
                    'confidence': image_result['confidence'],
                    'verdict': self._localize_deepfake_verdict(image_result['verdict'], language),
                    'reasoning': image_result['reasoning'],
                    'indicators': image_result.get('indicators', []),
                    'faces_detected': image_result.get('faces_detected', 0),
                    'limitations': image_result.get('limitations', ''),
                    'recommendations': self._get_deepfake_recommendations(risk_level, language)
                }
            except Exception as e:
                return {
                    'error': f'Image analysis failed: {str(e)}'
                }
        
        # For all other types, use orchestrator with language-aware LLM
        try:
            result = self.orchestrator.orchestrate_analysis(user_input, language=language)
            
            return {
                'type': result.input_type.value,
                'risk_level': result.risk_level,
                'confidence': result.confidence,
                'summary': result.summary,
                'reasoning': result.reasoning,
                'signals': [
                    {
                        'source': s.source,
                        'score': s.score,
                        'confidence': s.confidence,
                        'evidence': s.evidence
                    }
                    for s in result.signals
                ],
                'recommendations': result.recommendations,
                'uncertainties': result.uncertainty_notes
            }
        except Exception as e:
            return {
                'error': f'Analysis failed: {str(e)}'
            }
    
    def _localize_deepfake_verdict(self, verdict: str, language: str) -> str:
        """Localize deepfake verdicts"""
        if language != 'hi':
            return verdict
        
        translations = {
            'Likely Authentic': 'संभावित रूप से वास्तविक',
            'Likely Manipulated': 'संभावित रूप से छेड़छाड़ की गई',
            'Potentially Manipulated': 'संभावित रूप से छेड़छाड़ की गई',
            'Uncertain': 'अनिश्चित',
            'No faces detected': 'कोई चेहरा नहीं मिला'
        }
        
        return translations.get(verdict, verdict)
    
    def _get_voice_recommendations(self, risk_level: str, language: str = 'en'):
        """Generate recommendations for voice scam analysis"""
        if language == 'hi':
            recs = {
                'high': [
                    "कोई भी व्यक्तिगत या वित्तीय जानकारी प्रदान न करें",
                    "तुरंत कॉल काट दें",
                    "नंबर को अपने फ़ोन कैरियर और FTC को रिपोर्ट करें",
                    "नंबर को ब्लॉक करें"
                ],
                'medium': [
                    "संवेदनशील जानकारी साझा न करें",
                    "आधिकारिक चैनलों के माध्यम से कॉलर की पहचान सत्यापित करें",
                    "दबाव की रणनीति का उपयोग किए जाने पर कॉल समाप्त करें",
                    "कॉल विवरण दस्तावेज़ करें"
                ],
                'low': [
                    "अनिश्चित होने पर कॉलर की पहचान सत्यापित करें",
                    "अनुरोधों की पुष्टि के लिए आधिकारिक संपर्क विधियों का उपयोग करें",
                    "अपनी प्रवृत्ति पर भरोसा करें"
                ],
                'minimal': [
                    "विश्लेषण के आधार पर कॉल वैध प्रतीत होती है",
                    "मानक सावधानी अभी भी सलाह दी जाती है",
                    "किसी भी असामान्य अनुरोध को स्वतंत्र रूप से सत्यापित करें"
                ]
            }
        else:
            recs = {
                'high': [
                    "Do not provide any personal or financial information",
                    "Hang up immediately",
                    "Report the number to your phone carrier and FTC",
                    "Block the number"
                ],
                'medium': [
                    "Do not share sensitive information",
                    "Verify caller identity through official channels",
                    "End the call if pressure tactics are used",
                    "Document the call details"
                ],
                'low': [
                    "Verify caller identity if unsure",
                    "Use official contact methods to confirm requests",
                    "Trust your instincts"
                ],
                'minimal': [
                    "Call appears legitimate based on analysis",
                    "Standard caution still advised",
                    "Verify any unusual requests independently"
                ]
            }
        return recs.get(risk_level, recs['medium'])
    
    def _get_deepfake_recommendations(self, risk_level: str, language: str = 'en'):
        """Generate recommendations for deepfake analysis"""
        if language == 'hi':
            recs = {
                'high': [
                    "मीडिया में हेरफेर के संकेत दिखाई देते हैं",
                    "स्वतंत्र चैनलों के माध्यम से स्रोत सत्यापित करें",
                    "सत्यापन के बिना साझा या प्रवर्धित न करें",
                    "पेशेवर फोरेंसिक विश्लेषण पर विचार करें"
                ],
                'medium': [
                    "विश्लेषण अनिर्णायक - सावधानी बरतें",
                    "सामग्री पर भरोसा करने से पहले प्रामाणिकता सत्यापित करें",
                    "पुष्टि करने वाले स्रोतों की तलाश करें",
                    "संदर्भ और स्रोत विश्वसनीयता पर विचार करें"
                ],
                'minimal': [
                    "विश्लेषण के आधार पर मीडिया प्रामाणिक प्रतीत होता है",
                    "मानक सत्यापन प्रथाएं अभी भी लागू होती हैं",
                    "हेरफेर की संभावनाओं के प्रति जागरूक रहें"
                ]
            }
        else:
            recs = {
                'high': [
                    "Media shows signs of manipulation",
                    "Verify source through independent channels",
                    "Do not share or amplify without verification",
                    "Consider professional forensic analysis"
                ],
                'medium': [
                    "Analysis inconclusive - exercise caution",
                    "Verify authenticity before trusting content",
                    "Look for corroborating sources",
                    "Consider context and source credibility"
                ],
                'minimal': [
                    "Media appears authentic based on analysis",
                    "Standard verification practices still apply",
                    "Remain aware of manipulation possibilities"
                ]
            }
        return recs.get(risk_level, recs['medium'])
    
    def get_threat_news(self, days_back: int = 7, max_results: int = 20):
        """
        Get recent cyber threat news
        """
        try:
            news = self.news_intel.fetch_recent_threats(days_back, max_results)
            summary = self.news_intel.get_threat_summary(news)
            
            return {
                'news': news,
                'summary': summary
            }
        except Exception as e:
            return {
                'error': f'Failed to fetch threat news: {str(e)}',
                'news': [],
                'summary': {}
            }
    
    def _get_voice_recommendations(self, risk_level: str):
        """Generate recommendations for voice scam analysis"""
        recs = {
            'high': [
                "Do not provide any personal or financial information",
                "Hang up immediately",
                "Report the number to your phone carrier and FTC",
                "Block the number"
            ],
            'medium': [
                "Do not share sensitive information",
                "Verify caller identity through official channels",
                "End the call if pressure tactics are used",
                "Document the call details"
            ],
            'low': [
                "Verify caller identity if unsure",
                "Use official contact methods to confirm requests",
                "Trust your instincts"
            ],
            'minimal': [
                "Call appears legitimate based on analysis",
                "Standard caution still advised",
                "Verify any unusual requests independently"
            ]
        }
        return recs.get(risk_level, recs['medium'])

    def setup_agent(self):
        tools = [
            Tool(
                name="Domain Analyzer",
                func=self.analyze_domain,
                description="Analyzes a domain or URL for potential security threats"
            ),
            Tool(
                name="Message Analyzer",
                func=self.analyze_message,
                description="Analyzes a message for phishing attempts"
            ),
            Tool(
                name="Phone Number Analyzer",
                func=self.analyze_phone,
                description="Analyzes a phone number for potential threats"
            )
        ]
        self.agent = initialize_agent(tools, self.llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

    def analyze_phone(self, phone_number):

        phoneNumberVariants = generate_phone_number_variants(phone_number)
        searchData = checkPhoneLogic(phoneNumberVariants)

        template = """{Search_Data_Brave} \n\nPlease answer the user's question using only information from the search results. Include links to the relevant search result URLs within your answer. Keep your answer concise.

        User's question: Can you identify whether telephone number variants contains in this list {Phone_Number_Variants} is used for scams, phishing, or other suspicious activities? Highlight if the number is unsafe or write that there needs to be more information or if negative reviews and comments were not recorded in the first ten search results sites. 

        Assistant:
        """
        prompt = PromptTemplate(template=template, input_variables=["Search_Data_Brave", "Phone_Number_Variants"])
        chain = prompt | self.llm | RunnableLambda(lambda x: x.content)
        return chain.invoke({"Search_Data_Brave": searchData, "Phone_Number_Variants": phoneNumberVariants})
    
    

    def analyze_message(self, message):
        template = """
        Analyze the following message for potential phishing attempts:
        Message: {message}

        Provide your analysis, highlighting any suspicious elements:
        If message contains domain or email than also call Domain Analyzer tool, if contains phone number than call Phone Number Analyzer Tool
        """
        prompt = PromptTemplate(template=template, input_variables=["message"])
        chain = prompt | self.llm | RunnableLambda(lambda x: x.content)
        return chain.invoke({"message": message})

    def run(self):
        while True:
            user_input = input("Hi, this is an AI Agent Brama, who can help you check the security metrics and safety of the following resources: \nText messages, Site URL, Email, Phone number, and SMS. You can also use the educational mode to learn more about social engineering and cybersecurity threats, such as scams and phishing.\n\nEnter a URL, message, or write 'img', 'screenshot', or 'image' to attach an image, or 'education_mode' or 'quit' to exit: ")
            if user_input.lower() == 'quit':
                break

            # Check if user wants to attach a text file
            if user_input.lower() == 'file':
                file_path = input("Enter the path to the text file: ")
                with open(file_path, 'r') as file:
                    user_input = file.read()

            elif user_input.lower() == 'education_mode':
                educational_mode()
                continue

            # Extract domain from email address in user input
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b', user_input)
            if email_match:
                domain = email_match.group(1)
                domain_analysis = self.analyze_domain(domain)
                dmarc_analysis = checkDMARC(domain)
                user_input += f"\n\nDMARC analysis: {dmarc_analysis}"
            
            # Extract domain from user input
            domain_match = re.search(r'([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', user_input)
            if domain_match:
                domain = domain_match.group(1)
                if 'Domain Analyzer' in [tool.name for tool in self.agent.tools]:
                    domain_analysis = self.agent.run(f"Analyze the domain: {domain}")
                    user_input += f"\n\nDomain analysis: {domain_analysis}"

            # Extract phone number from user input
            phone_match = re.search(r'\+?\d[\d -]{8,15}\d', user_input)
            
            if phone_match:
                phone_number = phone_match.group(0)
                phone_analysis = self.analyze_phone(phone_number)
                user_input += f"\n\nPhone analysis: {phone_analysis}"

            # Check if user wants to attach a screenshot
            if 'img' in user_input.lower() or 'screenshot' in user_input.lower() or 'image' in user_input.lower():
                image_path = input("Enter the path to the image: ")
                image_analysis = self.describe_image(image_path)
                user_input += f"\n\nImage analysis: {image_analysis}"

            response = self.agent.run(user_input)
            

            # Analyze message content
            message_analysis = self.analyze_message(response)
            print(f"Message analysis: {message_analysis}")

if __name__ == "__main__":
    try:
        agent = CybersecurityAgent()
        agent.run()
    except ValueError as e:
        print(f"Error: {e}")
