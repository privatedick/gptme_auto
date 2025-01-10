
import asyncio
from task_processor import TaskProcessor
import json

async def main():
    # Läs konfiguration
    with open('task_queue.json', 'r') as f:
        config = json.load(f)
    
    # Skapa processor för varje meddelandetyp
    processors = {}
    for task_type, rate_limit in config['rate_limits'].items():
        processor = TaskProcessor(rate_limit)
        
        # Lägg till templates
        template = config['templates'][task_type]
        processor.template_manager.add_template(task_type, template)
        
        processors[task_type] = processor
    
    # Exempel på användning
    email_data = {
        "subject": "Test Email",
        "recipient": "test@example.com",
        "body": "This is a test email."
    }
    
    sms_data = {
        "phone": "+1234567890",
        "message": "Test SMS message"
    }
    
    notification_data = {
        "title": "Test",
        "message": "Test notification"
    }
    
    # Processera olika typer av meddelanden
    tasks = [
        processors['email'].process_task('email', 'email', email_data),
        processors['sms'].process_task('sms', 'sms', sms_data),
        processors['notification'].process_task(
            'notification',
            'notification',
            notification_data
        )
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Visa resultat och statistik
    for task_type, result in zip(['email', 'sms', 'notification'], results):
        print(f"\n{task_type.upper()} Result:")
        print(result)
        
        stats = processors[task_type].get_stats(task_type)
        print(f"Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
