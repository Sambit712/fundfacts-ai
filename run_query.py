import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from api.main import chat_endpoint, ChatRequest

async def main():
    query = "what is the nav of icici mutual fund?"
    print(f"Query    : {query}")
    print("-" * 60)
    req = ChatRequest(query=query)
    res = await chat_endpoint(req)
    print(f"Type     : {res['type']}")
    print(f"Answer   : {res['answer']}")
    print(f"Source   : {res.get('source')}")
    print(f"Updated  : {res.get('last_updated')}")
    print(f"Cached   : {res.get('cached', False)}")

asyncio.run(main())
