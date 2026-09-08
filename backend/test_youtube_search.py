from tools.youtube_tool import search_youtube


print("=" * 60)
print("AURA YOUTUBE DIRECT TEST")
print("=" * 60)

query = "Agentic AI"

print("\nSearching YouTube for:")
print(query)

result = search_youtube(
    query=query,
    max_results=5
)

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)

print(result)

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)