from main import ChatbotService

chatbot_service = ChatbotService()
chatbot_service.initialize_model()
print(chatbot_service.get_response("¿Cuál es tu función?"))
