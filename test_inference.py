import asyncio
from api.main import chat_endpoint, ChatRequest

async def run_tests():
    print("=== TEST 1: Factual Query (Fund mentioned) ===")
    req1 = ChatRequest(query="What is the NAV of HDFC Mid Cap?")
    res1 = await chat_endpoint(req1)
    print(res1)
    print("\n" + "="*50 + "\n")

    print("=== TEST 2: Factual Query (Broad) ===")
    req2 = ChatRequest(query="Which fund has the lowest expense ratio?")
    res2 = await chat_endpoint(req2)
    print(res2)
    print("\n" + "="*50 + "\n")

    print("=== TEST 3: Advisory Query (Keyword block) ===")
    req3 = ChatRequest(query="Should I invest in SBI Contra?")
    res3 = await chat_endpoint(req3)
    print(res3)
    print("\n" + "="*50 + "\n")

    print("=== TEST 4: Advisory Query (LLM intent) ===")
    # Avoiding blocked keywords directly, but asking an advisory question
    req4 = ChatRequest(query="Is UTI Innovation a solid bet for a new portfolio?")
    res4 = await chat_endpoint(req4)
    print(res4)
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
