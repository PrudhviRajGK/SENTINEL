"""
Voice Scam Analysis Module
Transcribes audio and detects scam patterns using OpenAI Whisper
"""

import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class VoiceScamAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Scam indicator patterns
        self.urgency_patterns = [
            r'\b(urgent|immediately|right now|act now|within \d+ (hours?|minutes?))\b',
            r'\b(expire|suspended|blocked|locked|terminated)\b',
            r'\b(last chance|final (notice|warning))\b'
        ]
        
        self.authority_patterns = [
            r'\b(bank|police|IRS|tax|government|FBI|officer|agent|department)\b',
            r'\b(legal action|arrest|warrant|court|lawsuit)\b',
            r'\b(verify your (identity|account|information))\b'
        ]
        
        self.payment_patterns = [
            r'\b(gift card|iTunes|Google Play|Amazon card|prepaid)\b',
            r'\b(wire transfer|Western Union|MoneyGram|cryptocurrency|bitcoin)\b',
            r'\b(pay (now|immediately)|send money|transfer funds)\b',
            r'\b(refund|prize|won|lottery|inheritance)\b'
        ]
        
        self.manipulation_patterns = [
            r'\b(don\'t tell anyone|keep this (private|confidential|secret))\b',
            r'\b(you\'re in trouble|serious consequences|penalty)\b',
            r'\b(congratulations|you\'ve been selected|lucky winner)\b'
        ]

    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file using OpenAI Whisper
        """
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return transcript
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    def detect_scam_indicators(self, transcript):
        """
        Analyze transcript for scam indicators
        Returns structured analysis with confidence scores
        """
        transcript_lower = transcript.lower()
        
        indicators = {
            'urgency': self._check_patterns(transcript_lower, self.urgency_patterns),
            'authority': self._check_patterns(transcript_lower, self.authority_patterns),
            'payment': self._check_patterns(transcript_lower, self.payment_patterns),
            'manipulation': self._check_patterns(transcript_lower, self.manipulation_patterns)
        }
        
        # Calculate confidence scores
        total_indicators = sum(len(matches) for matches in indicators.values())
        
        # Determine risk level based on indicator count and types
        if total_indicators >= 5 or (indicators['payment'] and indicators['urgency']):
            risk_level = 'high'
            confidence = min(85 + (total_indicators * 3), 98)
        elif total_indicators >= 3:
            risk_level = 'medium'
            confidence = 60 + (total_indicators * 5)
        elif total_indicators >= 1:
            risk_level = 'low'
            confidence = 30 + (total_indicators * 10)
        else:
            risk_level = 'minimal'
            confidence = 15
        
        return {
            'indicators': indicators,
            'total_indicator_count': total_indicators,
            'risk_level': risk_level,
            'confidence': confidence
        }

    def _check_patterns(self, text, patterns):
        """
        Check text against pattern list and return matches
        """
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        return matches

    def analyze_call(self, audio_file_path, language='en'):
        """
        Complete call analysis pipeline with multilingual support
        Returns structured analysis with transcript, indicators, and verdict
        
        Args:
            audio_file_path: Path to audio file
            language: Language for reasoning ('en' or 'hi')
        """
        try:
            # Step 1: Transcribe
            transcript = self.transcribe_audio(audio_file_path)
            
            # Step 2: Detect scam patterns
            scam_analysis = self.detect_scam_indicators(transcript)
            
            # Step 3: Generate AI reasoning (language-aware)
            reasoning = self._generate_reasoning(transcript, scam_analysis, language)
            
            return {
                'transcript': transcript,
                'scam_indicators': scam_analysis['indicators'],
                'total_indicators': scam_analysis['total_indicator_count'],
                'risk_level': scam_analysis['risk_level'],
                'confidence': scam_analysis['confidence'],
                'reasoning': reasoning,
                'verdict': self._generate_verdict(scam_analysis, language)
            }
            
        except Exception as e:
            raise Exception(f"Voice analysis failed: {str(e)}")

    def _generate_reasoning(self, transcript, analysis, language='en'):
        """
        Use GPT to generate human-readable reasoning in specified language
        CRITICAL: LLM must think natively in the target language
        """
        try:
            if language == 'hi':
                prompt = f"""इस फ़ोन कॉल ट्रांसक्रिप्ट का घोटाले के संकेतकों के लिए विश्लेषण करें।

ट्रांसक्रिप्ट: {transcript}

पहचाने गए संकेतक:
- तात्कालिकता वाक्यांश: {len(analysis['indicators']['urgency'])}
- प्राधिकरण प्रतिरूपण: {len(analysis['indicators']['authority'])}
- भुगतान दबाव: {len(analysis['indicators']['payment'])}
- हेरफेर रणनीति: {len(analysis['indicators']['manipulation'])}

एक संक्षिप्त, पेशेवर विश्लेषण प्रदान करें जो समझाता है:
1. कौन से पैटर्न पहचाने गए
2. वे संभावित घोटाले के व्यवहार को क्यों इंगित करते हैं
3. कॉलर का संभावित इरादा क्या है

इसे संक्षिप्त (3-4 वाक्य) और विश्लेषणात्मक रखें, अलार्मवादी नहीं।"""
            else:
                prompt = f"""Analyze this phone call transcript for scam indicators.

Transcript: {transcript}

Detected indicators:
- Urgency phrases: {len(analysis['indicators']['urgency'])}
- Authority impersonation: {len(analysis['indicators']['authority'])}
- Payment pressure: {len(analysis['indicators']['payment'])}
- Manipulation tactics: {len(analysis['indicators']['manipulation'])}

Provide a brief, professional analysis explaining:
1. What patterns were detected
2. Why they indicate potential scam behavior
3. What the caller's likely intent is

Keep it concise (3-4 sentences) and analytical, not alarmist."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Unable to generate detailed reasoning: {str(e)}"

    def _generate_verdict(self, analysis, language='en'):
        """
        Generate clear verdict based on analysis in specified language
        """
        risk = analysis['risk_level']
        confidence = analysis['confidence']
        
        if language == 'hi':
            verdicts = {
                'high': f"संभावित घोटाला कॉल ({confidence}% विश्वसनीयता)। कई लाल झंडे पहचाने गए।",
                'medium': f"संदिग्ध कॉल ({confidence}% विश्वसनीयता)। कई चिंताजनक संकेतक मौजूद हैं।",
                'low': f"संभावित रूप से वैध ({confidence}% विश्वसनीयता)। न्यूनतम घोटाले के संकेतक पहचाने गए।",
                'minimal': f"संभावित रूप से वैध ({confidence}% विश्वसनीयता)। कोई महत्वपूर्ण घोटाले के पैटर्न नहीं मिले।"
            }
        else:
            verdicts = {
                'high': f"Likely scam call ({confidence}% confidence). Multiple red flags detected.",
                'medium': f"Suspicious call ({confidence}% confidence). Several concerning indicators present.",
                'low': f"Potentially legitimate ({confidence}% confidence). Minimal scam indicators detected.",
                'minimal': f"Likely legitimate ({confidence}% confidence). No significant scam patterns found."
            }
        
        return verdicts.get(risk, "Unable to determine verdict")
