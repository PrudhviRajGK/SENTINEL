"""
Agent Orchestrator - Central Intelligence Layer
Coordinates tool selection, API calls, and reasoning
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class InputType(Enum):
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    MESSAGE = "message"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    UNKNOWN = "unknown"

@dataclass
class ThreatSignal:
    """Represents a single threat signal from an API/tool"""
    source: str
    score: float  # 0-100
    confidence: float  # 0-100
    evidence: str
    raw_data: Optional[Dict] = None

@dataclass
class AnalysisResult:
    """Structured analysis result"""
    input_type: InputType
    risk_level: str  # minimal, low, medium, high
    confidence: float  # 0-100
    summary: str
    reasoning: List[str]
    signals: List[ThreatSignal]
    recommendations: List[str]
    uncertainty_notes: List[str]
    raw_input: str

class AgentOrchestrator:
    """
    Central orchestrator that:
    1. Identifies input type
    2. Selects appropriate tools
    3. Weighs signals intelligently
    4. Produces reasoned verdicts
    """
    
    def __init__(self, llm, tools_dict):
        """
        Args:
            llm: Language model for reasoning
            tools_dict: Dictionary of available tools/analyzers
        """
        self.llm = llm
        self.tools = tools_dict
        
        # Threat scoring weights
        self.weights = {
            'virustotal': 0.35,
            'urlhaus': 0.25,
            'abuseipdb': 0.20,
            'urlscan': 0.15,
            'serper': 0.10,
            'dmarc': 0.15,
            'phone_search': 0.20,
            'voice_analysis': 0.40,
            'llm_analysis': 0.05
        }
        
    def identify_input_type(self, user_input: str) -> InputType:
        """
        Intelligently identify what type of input this is
        """
        input_lower = user_input.lower().strip()
        
        # URL patterns
        if re.search(r'https?://', input_lower) or re.search(r'\b[a-z0-9-]+\.[a-z]{2,}\b', input_lower):
            return InputType.URL
        
        # Email patterns
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_input):
            return InputType.EMAIL
        
        # Phone patterns
        if re.search(r'\+?\d[\d\s\-\(\)]{8,}\d', user_input):
            return InputType.PHONE
        
        # Default to message
        return InputType.MESSAGE
    
    def select_tools(self, input_type: InputType, input_text: str) -> List[str]:
        """
        Decide which tools to use based on input type
        Returns list of tool names to invoke
        """
        tool_map = {
            InputType.URL: ['virustotal', 'urlhaus', 'urlscan', 'llm_analysis', 'news_correlation'],
            InputType.EMAIL: ['virustotal', 'dmarc', 'llm_analysis', 'news_correlation'],
            InputType.PHONE: ['phone_search', 'llm_analysis'],
            InputType.MESSAGE: ['llm_analysis', 'serper', 'news_correlation'],
            InputType.IMAGE: ['image_ocr', 'deepfake_detection', 'llm_analysis'],
            InputType.VOICE: ['voice_analysis', 'llm_analysis'],
            InputType.VIDEO: ['deepfake_detection', 'llm_analysis']
        }
        
        selected = tool_map.get(input_type, ['llm_analysis'])
        
        # Filter to only available tools
        return [tool for tool in selected if tool in self.tools]
    
    def calculate_weighted_risk(self, signals: List[ThreatSignal]) -> Dict[str, Any]:
        """
        Calculate weighted risk score from multiple signals
        This is the core intelligence - no single API dictates the verdict
        """
        if not signals:
            return {
                'risk_score': 0,
                'risk_level': 'minimal',
                'confidence': 20,
                'reasoning': ['No threat signals detected']
            }
        
        # Calculate weighted score
        total_weight = 0
        weighted_sum = 0
        confidence_sum = 0
        
        for signal in signals:
            weight = self.weights.get(signal.source.lower(), 0.05)
            weighted_sum += signal.score * weight * (signal.confidence / 100)
            total_weight += weight
            confidence_sum += signal.confidence
        
        # Normalize
        risk_score = (weighted_sum / total_weight) if total_weight > 0 else 0
        avg_confidence = confidence_sum / len(signals) if signals else 0
        
        # Determine risk level with nuance
        if risk_score >= 75:
            risk_level = 'high'
        elif risk_score >= 50:
            risk_level = 'medium'
        elif risk_score >= 25:
            risk_level = 'low'
        else:
            risk_level = 'minimal'
        
        # Generate reasoning
        reasoning = self._generate_risk_reasoning(signals, risk_score)
        
        return {
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'confidence': round(avg_confidence, 1),
            'reasoning': reasoning
        }
    
    def _generate_risk_reasoning(self, signals: List[ThreatSignal], risk_score: float) -> List[str]:
        """
        Generate human-readable reasoning for the risk assessment
        """
        reasoning = []
        
        # Group signals by score
        high_risk_signals = [s for s in signals if s.score >= 70]
        medium_risk_signals = [s for s in signals if 40 <= s.score < 70]
        low_risk_signals = [s for s in signals if s.score < 40]
        
        if high_risk_signals:
            sources = ', '.join([s.source for s in high_risk_signals])
            reasoning.append(f"Strong threat indicators from {sources}")
        
        if medium_risk_signals:
            sources = ', '.join([s.source for s in medium_risk_signals])
            reasoning.append(f"Moderate concerns flagged by {sources}")
        
        if low_risk_signals:
            sources = ', '.join([s.source for s in low_risk_signals])
            reasoning.append(f"Minimal indicators from {sources}")
        
        # Check for signal agreement
        if len(signals) >= 2:
            scores = [s.score for s in signals]
            score_variance = max(scores) - min(scores)
            
            if score_variance < 20:
                reasoning.append("Multiple sources show consistent assessment")
            else:
                reasoning.append("Sources show mixed signals - verdict requires caution")
        
        return reasoning if reasoning else ["Insufficient data for detailed reasoning"]
    
    def generate_recommendations(self, risk_level: str, input_type: InputType, 
                                 signals: List[ThreatSignal], language: str = 'en') -> List[str]:
        """
        Generate actionable recommendations based on risk and context
        Language-aware recommendations
        """
        if language == 'hi':
            base_recommendations = {
                'high': [
                    "इस सामग्री के साथ इंटरैक्ट न करें",
                    "तुरंत अपनी सुरक्षा टीम को रिपोर्ट करें",
                    "यदि संभव हो तो स्रोत को ब्लॉक करें"
                ],
                'medium': [
                    "अत्यधिक सावधानी के साथ आगे बढ़ें",
                    "स्वतंत्र चैनलों के माध्यम से सत्यापित करें",
                    "संवेदनशील जानकारी प्रदान न करें"
                ],
                'low': [
                    "मानक सुरक्षा प्रथाओं का पालन करें",
                    "अनिश्चित होने पर प्रेषक की पहचान सत्यापित करें",
                    "अतिरिक्त संदिग्ध गतिविधि की निगरानी करें"
                ],
                'minimal': [
                    "उपलब्ध डेटा के आधार पर सामग्री वैध प्रतीत होती है",
                    "सामान्य सुरक्षा जागरूकता बनाए रखें",
                    "व्यवहार बदलने पर रिपोर्ट करें"
                ]
            }
        else:
            base_recommendations = {
                'high': [
                    "Do not interact with this content",
                    "Report to your security team immediately",
                    "Block the source if possible"
                ],
                'medium': [
                    "Proceed with extreme caution",
                    "Verify through independent channels",
                    "Do not provide sensitive information"
                ],
                'low': [
                    "Exercise standard security practices",
                    "Verify sender identity if unsure",
                    "Monitor for additional suspicious activity"
                ],
                'minimal': [
                    "Content appears legitimate based on available data",
                    "Maintain general security awareness",
                    "Report if behavior changes"
                ]
            }
        
        recommendations = base_recommendations.get(risk_level, [])
        
        # Add context-specific recommendations (language-aware)
        if input_type == InputType.PHONE:
            if risk_level in ['high', 'medium']:
                if language == 'hi':
                    recommendations.append("कॉल वापस न करें या कॉलबैक जानकारी प्रदान न करें")
                else:
                    recommendations.append("Do not return the call or provide callback information")
        
        if input_type == InputType.EMAIL:
            if risk_level in ['high', 'medium']:
                if language == 'hi':
                    recommendations.append("लिंक पर क्लिक न करें या अटैचमेंट डाउनलोड न करें")
                else:
                    recommendations.append("Do not click links or download attachments")
        
        return recommendations
    
    def identify_uncertainty(self, signals: List[ThreatSignal], 
                            risk_assessment: Dict) -> List[str]:
        """
        Explicitly identify areas of uncertainty
        This is critical for honest AI - we admit what we don't know
        """
        uncertainties = []
        
        # Low confidence signals
        low_conf_signals = [s for s in signals if s.confidence < 60]
        if low_conf_signals:
            sources = ', '.join([s.source for s in low_conf_signals])
            uncertainties.append(f"Low confidence data from {sources}")
        
        # Conflicting signals
        if len(signals) >= 2:
            scores = [s.score for s in signals]
            if max(scores) - min(scores) > 40:
                uncertainties.append("Conflicting assessments across sources")
        
        # Limited data
        if len(signals) < 2:
            uncertainties.append("Limited data sources available for analysis")
        
        # Low overall confidence
        if risk_assessment['confidence'] < 50:
            uncertainties.append("Overall confidence is below threshold for definitive verdict")
        
        return uncertainties
    
    def orchestrate_analysis(self, user_input: str, 
                            additional_context: Optional[Dict] = None,
                            language: str = 'en') -> AnalysisResult:
        """
        Main orchestration method with multilingual support
        Coordinates the entire analysis pipeline
        
        Args:
            user_input: The content to analyze
            additional_context: Optional additional context
            language: Language for LLM reasoning ('en' or 'hi')
        """
        # Step 1: Identify input type
        input_type = self.identify_input_type(user_input)
        
        # Step 2: Select appropriate tools
        selected_tools = self.select_tools(input_type, user_input)
        
        # Step 3: Execute tools and collect signals
        signals = []
        for tool_name in selected_tools:
            try:
                tool = self.tools.get(tool_name)
                if tool:
                    signal = tool(user_input)
                    if signal:
                        signals.append(signal)
            except Exception as e:
                # Log but don't fail entire analysis
                print(f"Tool {tool_name} failed: {e}")
        
        # Step 4: Calculate weighted risk
        risk_assessment = self.calculate_weighted_risk(signals)
        
        # Step 5: Generate recommendations (language-aware)
        recommendations = self.generate_recommendations(
            risk_assessment['risk_level'],
            input_type,
            signals,
            language
        )
        
        # Step 6: Identify uncertainties
        uncertainties = self.identify_uncertainty(signals, risk_assessment)
        
        # Step 7: Generate summary using LLM (language-aware)
        summary = self._generate_summary(
            user_input,
            input_type,
            risk_assessment,
            signals,
            language
        )
        
        return AnalysisResult(
            input_type=input_type,
            risk_level=risk_assessment['risk_level'],
            confidence=risk_assessment['confidence'],
            summary=summary,
            reasoning=risk_assessment['reasoning'],
            signals=signals,
            recommendations=recommendations,
            uncertainty_notes=uncertainties,
            raw_input=user_input[:200]  # Truncate for safety
        )
    
    def _generate_summary(self, user_input: str, input_type: InputType,
                         risk_assessment: Dict, signals: List[ThreatSignal],
                         language: str = 'en') -> str:
        """
        Use LLM to generate human-readable summary in specified language
        CRITICAL: LLM must think and reason natively in the target language
        """
        try:
            signal_summary = "\n".join([
                f"- {s.source}: {s.evidence} (score: {s.score}, confidence: {s.confidence}%)"
                for s in signals
            ])
            
            # Language-specific system prompt
            if language == 'hi':
                system_prompt = """आप एक पेशेवर साइबर सुरक्षा विश्लेषक हैं। 
आपको हिंदी में स्पष्ट, तकनीकी और तटस्थ भाषा में जवाब देना है।
अनौपचारिक भाषा या स्लैंग का उपयोग न करें।
साइबर सुरक्षा तर्क को स्पष्ट रूप से समझाएं।"""
                
                prompt = f"""{system_prompt}

इस सुरक्षा मूल्यांकन का विश्लेषण करें और एक संक्षिप्त, पेशेवर सारांश प्रदान करें।

इनपुट प्रकार: {input_type.value}
जोखिम स्तर: {risk_assessment['risk_level']}
जोखिम स्कोर: {risk_assessment['risk_score']}/100
विश्वसनीयता: {risk_assessment['confidence']}%

पहचाने गए संकेत:
{signal_summary}

2-3 वाक्यों में एक सारांश प्रदान करें जो:
1. निर्णय को स्पष्ट रूप से बताता है
2. मुख्य तर्क की व्याख्या करता है
3. पेशेवर, विश्लेषणात्मक स्वर बनाए रखता है (कोई अलार्मवाद नहीं)

सारांश:"""
            else:
                prompt = f"""Analyze this security assessment and provide a brief, professional summary.

Input type: {input_type.value}
Risk level: {risk_assessment['risk_level']}
Risk score: {risk_assessment['risk_score']}/100
Confidence: {risk_assessment['confidence']}%

Signals detected:
{signal_summary}

Provide a 2-3 sentence summary that:
1. States the verdict clearly
2. Explains the key reasoning
3. Maintains professional, analytical tone (no alarmism)

Summary:"""

            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            # Fallback summary (language-aware)
            if language == 'hi':
                return f"जोखिम स्तर: {risk_assessment['risk_level']} ({risk_assessment['confidence']}% विश्वसनीयता)। {risk_assessment['reasoning'][0] if risk_assessment['reasoning'] else 'विश्लेषण पूर्ण।'}"
            else:
                return f"Risk level: {risk_assessment['risk_level']} ({risk_assessment['confidence']}% confidence). {risk_assessment['reasoning'][0] if risk_assessment['reasoning'] else 'Analysis complete.'}"
