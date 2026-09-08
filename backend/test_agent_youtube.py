from agent.agent import run_agent


print("================================")
print("AURA YOUTUBE AGENT TEST")
print("================================")


query = "Find the latest Generative AI news on YouTube"


print("\nUser:")
print(query)


print("\nRunning AURA...\n")


result = run_agent(query)


print("================================")
print("ROUTE")
print("================================")

print(result["route"])


print("\n================================")
print("ANSWER")
print("================================")

print(result["answer"])


print("\n================================")
print("TEST COMPLETE")
print("================================")