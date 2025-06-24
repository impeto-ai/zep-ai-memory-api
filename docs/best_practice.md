---
title: Performance Optimization Guide
description: Best practices for optimizing Zep performance in production
slug: performance
---

This guide covers best practices for optimizing Zep's performance in production environments.

## Reuse the Zep SDK Client

The Zep SDK client maintains an HTTP connection pool that enables connection reuse, significantly reducing latency by avoiding the overhead of establishing new connections. To optimize performance:

- Create a single client instance and reuse it across your application
- Avoid creating new client instances for each request or function
- Consider implementing a client singleton pattern in your application
- For serverless environments, initialize the client outside the handler function

## Optimizing Memory Operations

The `memory.add` and `memory.get` methods are optimized for conversational messages and low-latency retrieval. For optimal performance:

- Keep individual messages under 10K characters
- Use `graph.add` for larger documents, tool outputs, or business data
- Consider chunking large documents before adding them to the graph (the `graph.add` endpoint has a 10,000 character limit)
- Remove unnecessary metadata or content before persistence
- For bulk document ingestion, process documents in parallel while respecting rate limits

```python
# Recommended for conversations
zep_client.memory.add(
    session_id="session_123",
    message={
        "role": "human",
        "content": "What's the weather like today?"
    }
)

# Recommended for large documents
await zep_client.graph.add(
    data=document_content,  # Your chunked document content
    user_id=user_id,       # Or group_id for group graphs
    type="text"            # Can be "text", "message", or "json"
)
```

### Get the memory context string sooner

Additionally, you can request the memory context directly in the response to the `memory.add()` call. 
This optimization eliminates the need for a separate `memory.get()` if you happen to only need the context. 
Read more about [Memory Context](/concepts/#memory-context).

In this scenario you can pass in the `return_context=True` flag to the `memory.add()` method. 
Zep will perform a user graph search right after persisting the memory and return the context relevant to the recently added memory. 

<Tabs group="add-with-context">
<Tab title="Python" group-key="python">
```python
memory_response = await zep_client.memory.add(
    session_id=session_id,
    messages=messages,
    return_context=True
)

context = memory_response.context
```
</Tab>

<Tab title="TypeScript" group-key="typescript">
```typescript
const memoryResponse = await zepClient.memory.add(sessionId, {
    messages: messages,
    returnContext: true
});

const context = memoryResponse.context;
```
</Tab>
<Tab title="Go" group-key="go">
```golang
memoryResponse, err := zepClient.Memory.Add(
    context.TODO(),
    sessionID,
    &zep.AddMemoryRequest{
        Messages: messages,
        ReturnContext: zep.Bool(true),
    },
)
if err != nil {
    // handle error
}
memoryContext := memoryResponse.Context
```
</Tab>
</Tabs>

<Tip>Read more in the [Memory SDK Reference](/sdk-reference/memory#add)</Tip>

## Optimizing Search Queries


Zep uses hybrid search combining semantic similarity and BM25 full-text search. For optimal performance:

- Keep your queries concise. Queries are automatically truncated to 8,192 tokens (approximately 32,000 Latin characters)
- Longer queries may not improve search quality and will increase latency
- Consider breaking down complex searches into smaller, focused queries
- Use specific, contextual queries rather than generic ones

Best practices for search:

- Keep search queries concise and specific
- Structure queries to target relevant information
- Use natural language queries for better semantic matching
- Consider the scope of your search (user vs group graphs)

```python
# Recommended - concise query
results = await zep_client.graph.search(
    user_id=user_id,  # Or group_id for group graphs
    query="project requirements discussion"
)

# Not recommended - overly long query
results = await zep_client.graph.search(
    user_id=user_id,
    query="very long text with multiple paragraphs..."  # Will be truncated
)
```

## Summary

- Reuse Zep SDK client instances to optimize connection management
- Use appropriate methods for different types of content (`memory.add` for conversations, `graph.add` for large documents)
- Keep search queries focused and under the token limit for optimal performance

---
title: Adding JSON Best Practices
description: Best practices for preparing JSON data for ingestion into Zep
slug: adding-json-best-practices
---
Adding JSON to Zep without adequate preparation can lead to unexpected results. For instance, adding a large JSON without dividing it up can lead to a graph with very few nodes. Below, we go over what type of JSON works best with Zep, and techniques you can use to ensure your JSON fits these criteria.

## Key Criteria

At a high level, ingestion of JSON into Zep works best when these criteria are met:

1. **JSON is not too large**: Large JSON should be divided into pieces, adding each piece separately to Zep.  
2. **JSON is not deeply nested**: Deeply nested JSON (more than 3 to 4 levels) should be flattened while preserving information.  
3. **JSON is understandable in isolation**: The JSON should include all the information needed to understand the data it represents. This might mean adding descriptions or understandable attribute names where relevant.  
4. **JSON represents a unified entity**: The JSON should ideally represent a unified entity, with ID, name, and description fields. Zep treats the JSON as a whole as a "first class entity", creating branching entities off of the main JSON entity from the JSON's attributes.

## JSON that is too large

### JSON with too many attributes

**Recommendation**: Split up the properties among several instances of the object. Each instance should duplicate the `id`, `name`, and `description` fields, or similar fields that tie each chunk to the same object, and then have 3 to 4 additional properties.

### JSON with too many list elements

**Recommendation**: Split up the list into its elements, ensuring you add additional fields to contextualize each element if needed. For instance, if the key of the list is "cars", then you should add a field which indicates that the list item is a car.

### JSON with large strings

**Recommendation**: A very long string might be better added to the graph as unstructured text instead of JSON. You may need to add a sentence or two to contextualize the unstructured text with respect to the rest of the JSON, since they would be added separately. And if it is very long, you would want to employ document chunking methods, such as described by Anthropic [here](https://www.anthropic.com/news/contextual-retrieval).

## JSON that is deeply nested

**Recommendation**: For each deeply nested value In the JSON, create a flattened JSON piece for that value specifically. For instance, if your JSON alternates between dictionaries and lists for 5 to 6 levels with a single value at the bottom, then the flattened version would have an attribute for the value, and an attribute to convey any information from each of the keys from the original JSON.

## JSON that is not understandable in isolation

**Recommendation**: Add descriptions or helpful/interpretable attribute names where relevant.

## JSON that is not a unified entity

**Recommendation**: Add an `id`, `name`, and `description` field to the JSON. Additionally, if the JSON essentially represents two or more objects, split it up.

## Dealing with a combination of the above

**Recommendation**: First, deal with the fact that the JSON is too large and/or too deeply nested by iteratively applying these recommendations (described above) from the top down: splitting up attributes, splitting up lists, flattening deeply nested JSON, splitting out any large text documents. For example, if your JSON has a lot of attributes and one of those attributes is a long list, then you should first split up the JSON by the attributes, and then split up the JSON piece that contains the long list by splitting the list elements.

After applying the iterative transformations, you should have a list of candidate JSON, each of which is not too large or too deeply nested. As the last step, you should ensure that each JSON in the list is understandable in isolation and represents a unified entity by applying the recommendations above. 