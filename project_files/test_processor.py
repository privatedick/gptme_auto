
import asyncio
from task_processor import TaskProcessor

async def main():
    processor = TaskProcessor(rate_limit=5)  # Sätt låg gräns för test
    
    # Lägg till några templates
    processor.template_manager.add_template(
        "greeting",
        "Hello {name}! Welcome to {project}."
    )
    
    # Testa några anrop
    tasks = []
    for i in range(10):
        task = processor.process_task(
            "greeting",
            "greeting",
            {"name": f"User{i}", "project": "TestProject"}
        )
        tasks.append(task)
    
    # Kör alla tasks
    results = await asyncio.gather(*tasks)
    
    # Visa resultat
    print("Results:", [r for r in results if r])
    print("Stats:", processor.get_stats("greeting"))

if __name__ == "__main__":
    asyncio.run(main())
