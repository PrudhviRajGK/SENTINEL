"""
Sentinel Flask Backend
Enterprise threat intelligence API
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import base64
from io import BytesIO
from PIL import Image

# Load environment variables
load_dotenv()

# Import agent
from agent import CybersecurityAgent
from services.twilio_client import TwilioService

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Initialize agent
try:
    agent = CybersecurityAgent()
except ValueError as e:
    print(f"Warning: Agent initialization failed - {e}")
    agent = None

# Initialize Twilio service
twilio_service = TwilioService()

@app.route('/')
def index():
    """Serve the main frontend"""
    return send_from_directory('frontend', 'index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent_initialized': agent is not None
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    REFACTORED: Agentic analysis endpoint with multilingual support
    Uses orchestrator for intelligent, reasoned verdicts
    """
    if not agent:
        return jsonify({
            'error': 'Agent not initialized. Please check API keys.'
        }), 500

    try:
        data = request.get_json()
        input_text = data.get('input', '').strip()
        language = data.get('language', 'en')  # Get language from request

        if not input_text:
            return jsonify({
                'error': 'Input is required'
            }), 400

        # Use new agentic analysis with language
        result = agent.agentic_analyze(input_text, language=language)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify(result)

    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({
            'error': 'Analysis failed. Please try again.'
        }), 500

@app.route('/api/analyze/image', methods=['POST'])
def analyze_image():
    """
    REFACTORED: Analyze uploaded image with agentic reasoning
    """
    if not agent:
        return jsonify({
            'error': 'Agent not initialized. Please check API keys.'
        }), 500

    try:
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided'
            }), 400

        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400

        # Save temporarily and analyze
        image = Image.open(file.stream)
        temp_path = '/tmp/sentinel_temp_image.jpg'
        image.save(temp_path)

        # Describe image using agent
        image_description = agent.describe_image(temp_path)

        # Use agentic analysis on extracted text
        result = agent.agentic_analyze(image_description)
        
        # Add extracted text to result
        result['extracted_text'] = image_description

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify(result)

    except Exception as e:
        print(f"Image analysis error: {e}")
        return jsonify({
            'error': 'Image analysis failed. Please try again.'
        }), 500

@app.route('/api/analyze/voice', methods=['POST'])
def analyze_voice():
    """
    NEW: Analyze voice recording for scam detection
    Accepts audio files (WAV, MP3, M4A)
    """
    if not agent:
        return jsonify({
            'error': 'Agent not initialized. Please check API keys.'
        }), 500

    try:
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No audio file provided'
            }), 400

        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400

        # Save temporarily
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'mp3'
        temp_path = f'/tmp/sentinel_voice.{file_ext}'
        file.save(temp_path)

        # Analyze using agentic voice analysis
        result = agent.agentic_analyze(temp_path, input_type_hint='voice')

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify(result)

    except Exception as e:
        print(f"Voice analysis error: {e}")
        return jsonify({
            'error': 'Voice analysis failed. Please try again.'
        }), 500

@app.route('/api/analyze/video', methods=['POST'])
def analyze_video():
    """
    NEW: Analyze video for deepfake detection
    Accepts video files (MP4, AVI, MOV, MKV)
    """
    if not agent:
        return jsonify({
            'error': 'Agent not initialized. Please check API keys.'
        }), 500

    try:
        if 'video' not in request.files:
            return jsonify({
                'error': 'No video file provided'
            }), 400

        file = request.files['video']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400

        # Save temporarily
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'mp4'
        temp_path = f'/tmp/sentinel_video.{file_ext}'
        file.save(temp_path)

        # Analyze using deepfake detection
        result = agent.agentic_analyze(temp_path, input_type_hint='video')

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify(result)

    except Exception as e:
        print(f"Video analysis error: {e}")
        return jsonify({
            'error': 'Video analysis failed. Please try again.'
        }), 500

@app.route('/api/analyze/image/deepfake', methods=['POST'])
def analyze_image_deepfake():
    """
    NEW: Analyze image specifically for deepfake detection
    """
    if not agent:
        return jsonify({
            'error': 'Agent not initialized. Please check API keys.'
        }), 500

    try:
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided'
            }), 400

        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400

        # Save temporarily
        image = Image.open(file.stream)
        temp_path = '/tmp/sentinel_deepfake_image.jpg'
        image.save(temp_path)

        # Analyze for deepfakes
        result = agent.agentic_analyze(temp_path, input_type_hint='image_deepfake')

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        return jsonify(result)

    except Exception as e:
        print(f"Deepfake analysis error: {e}")
        return jsonify({
            'error': 'Deepfake analysis failed. Please try again.'
        }), 500

@app.route('/api/threat-news', methods=['GET'])
def get_threat_news():
    """
    NEW: Get recent cyber threat news
    """
    if not agent:
        return jsonify({
            'error': 'Agent not initialized. Please check API keys.'
        }), 500

    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        result = agent.get_threat_news(days_back=days, max_results=limit)
        
        return jsonify(result)

    except Exception as e:
        print(f"Threat news error: {e}")
        return jsonify({
            'error': 'Failed to fetch threat news',
            'news': [],
            'summary': {}
        }), 500

@app.route('/api/omnichannel/status', methods=['GET'])
def omnichannel_status():
    """
    Get omnichannel availability status
    """
    return jsonify({
        'web': True,
        'sms': twilio_service.is_enabled(),
        'whatsapp': twilio_service.is_enabled(),
        'voice': True  # Whisper is always available if OpenAI key is set
    })

@app.route('/api/omnichannel/twilio/inbound', methods=['POST'])
def twilio_inbound():
    """
    ENTERPRISE-GRADE: Webhook endpoint for incoming Twilio messages (SMS/WhatsApp)
    
    Architecture:
    - Single unified agent core
    - Conversation memory per phone number
    - Language detection (English/Hindi)
    - Professional, analyst-style responses
    - No emojis, no slang, no alarmist language
    """
    if not agent:
        # Graceful fallback - never expose internal errors
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 503
    
    if not twilio_service.is_enabled():
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 503
    
    try:
        # Clean up expired sessions periodically
        twilio_service.cleanup_expired_sessions()
        
        # Parse incoming message
        message_data = twilio_service.parse_incoming_message(request.values)
        
        user_input = message_data['body'].strip()
        sender = message_data['from']
        channel = message_data['channel']
        
        # Handle empty messages
        if not user_input:
            fallback_msg = "Please send a URL, message, or phone number to analyze." if twilio_service.detect_language("") == 'en' else "कृपया विश्लेषण के लिए URL, संदेश या फ़ोन नंबर भेजें।"
            
            twilio_service.send_message(
                to=sender,
                body=fallback_msg,
                channel=channel
            )
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
        # Get conversation context
        context_summary = twilio_service.get_conversation_context(sender)
        
        # Normalize message for unified agent
        normalized = twilio_service.normalize_message(message_data, context_summary)
        
        language = normalized['language']
        
        # Process through UNIFIED AGENT CORE
        # Same intelligence as web chatbot - no separate logic
        try:
            result = agent.agentic_analyze(
                user_input,
                language=language
            )
        except Exception as analysis_error:
            # Graceful fallback - never expose stack traces
            print(f"Agent analysis error: {analysis_error}")
            
            fallback_msg = "I couldn't analyze this message properly. Please try again." if language == 'en' else "मैं इस संदेश का ठीक से विश्लेषण नहीं कर सका। कृपया पुनः प्रयास करें।"
            
            twilio_service.send_message(
                to=sender,
                body=fallback_msg,
                channel=channel
            )
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
        # Format response for SMS (concise, professional)
        response_text = twilio_service.format_response_for_sms(result, language)
        
        # Update conversation memory
        twilio_service.update_conversation(
            phone_number=sender,
            user_message=user_input,
            agent_response=response_text,
            context={
                'last_risk_level': result.get('risk_level', 'unknown'),
                'last_analysis_type': result.get('type', 'text')
            }
        )
        
        # Send response via Twilio
        send_result = twilio_service.send_message(
            to=sender,
            body=response_text,
            channel=channel
        )
        
        if not send_result['success']:
            # Log failure but don't expose to user
            print(f"Twilio send failed for {sender[:10]}...")
        
        # Return empty TwiML response (Twilio expects this)
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
    except Exception as e:
        # Catch-all error handler - never expose internals
        print(f"Twilio webhook error: {e}")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 500

@app.route('/api/education/questions', methods=['GET'])
def get_questions():
    """
    Get educational questions
    """
    try:
        from educationalModuleRAG import QUESTIONS
        return jsonify({
            'questions': QUESTIONS[:10],  # Return first 10 questions
            'total': len(QUESTIONS)
        })
    except Exception as e:
        print(f"Error loading questions: {e}")
        return jsonify({
            'error': 'Failed to load questions'
        }), 500

@app.route('/api/education/answer', methods=['POST'])
def check_answer():
    """
    Check educational answer
    """
    if not agent:
        return jsonify({
            'error': 'Agent not initialized. Please check API keys.'
        }), 500

    try:
        data = request.get_json()
        question = data.get('question', '')
        answer = data.get('answer', '')

        if not question or not answer:
            return jsonify({
                'error': 'Question and answer are required'
            }), 400

        # Use agent to evaluate answer
        prompt = f"""
        Question: {question}
        User's Answer: {answer}
        
        Evaluate the user's answer and provide:
        1. Whether it's correct, partially correct, or incorrect
        2. A brief explanation
        3. The correct answer if needed
        
        Be constructive and educational.
        """

        feedback = agent.llm.invoke(prompt)
        
        return jsonify({
            'feedback': feedback.content if hasattr(feedback, 'content') else str(feedback)
        })

    except Exception as e:
        print(f"Answer checking error: {e}")
        return jsonify({
            'error': 'Failed to check answer'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"""
    ╔══════════════════════════════════════════╗
    ║   Sentinel - Enterprise Threat Intel    ║
    ╚══════════════════════════════════════════╝
    
    Server running on: http://localhost:{port}
    Agent initialized: {agent is not None}
    Agentic Mode: ENABLED
    Voice Analysis: ENABLED
    
    Omnichannel Status:
    - Web: ✓ Enabled
    - SMS: {'✓ Enabled' if twilio_service.is_enabled() else '✗ Disabled (configure Twilio)'}
    - WhatsApp: {'✓ Enabled' if twilio_service.is_enabled() else '✗ Disabled (configure Twilio)'}
    
    Press CTRL+C to stop
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)

