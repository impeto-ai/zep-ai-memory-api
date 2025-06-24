---
title: Key Concepts
subtitle: 'Understanding Zep''s Memory, Knowledge Graph, and Data Integration.'
slug: concepts
---

<Tip>
Looking to just get coding? Check out our [Quickstart](/quickstart).
</Tip>


## Summary

| Concept | Description | Docs |
| ------- | ----------- | ---- |
| Knowledge Graph | Zep's memory store for agents. Nodes represent entities, edges represent facts/relationships. The graph updates dynamically in response to new data. | [Docs](/understanding-the-graph) |
| Memory Context String | Optimized string containing facts and entities from the knowledge graph most relevant to the current session. Also contains dates when facts became valid and invalid. Provide this to your chatbot as "memory". | [Docs](/concepts#memory-context) |
| Fact Invalidation | When new data invalidates a prior fact, the time the fact became invalid is stored on that fact's edge in the knowledge graph. | [Docs](/facts) |
| JSON/text/message | Types of data that can be ingested into the knowledge graph. Can represent business data, documents, chat messages, emails, etc. | [Docs](/adding-data-to-the-graph#adding-message-data) |
| Custom entity types | Feature allowing use of Pydantic-like classes to customize creation/retrieval of entities in the knowledge graph.| [Docs](/entity-types) |
| User | Create a user in Zep to represent an individual using your application. Each user has their own knowledge graph.| [Docs](/users) |
| Sessions | Conversation threads of a user. By default, all messages added to any session of that user are ingested into that user's knowledge graph. | [Docs](/sessions) |
| Group | Used for creating an arbitrary knowledge graph that is not necessarily tied to a user. Useful for memory shared by a "group" of users.| [Docs](/groups) |
| `memory.add` & `graph.add` | High level and low level methods for adding data to the knowledge graph.| [Docs](/concepts#using-memoryadd) |
| `memory.get` & `graph.search` | High level and low level methods for retrieving from the knowledge graph. | [Docs](/concepts#using-memoryget) |
| Fact Ratings | Feature for rating and filtering facts by relevance to your use case.| [Docs](/facts#rating-facts-for-relevancy) |


Zep is a memory layer for AI assistants and agents that continuously learns from user interactions and changing business data. Zep ensures that your Agent has a complete and holistic view of the user, enabling you to build more personalized and accurate user experiences.

Using [user chat histories and business data](#business-data-vs-chat-message-data), Zep automatically constructs a [knowledge graph](#the-knowledge-graph) for each of your users. The knowledge graph contains entities, relationships, and facts related to your user. As facts change or are superseded, [Zep updates the graph](#managing-changes-in-facts-over-time) to reflect their new state. Using Zep, you can [build prompts](#how-zep-fits-into-your-application) that provide your agent with the information it needs to personalize responses and solve problems. Ensuring your prompts have the right information reduces hallucinations, improves recall, and reduces the cost of LLM calls.

<lite-vimeo videoid="1021963693"></lite-vimeo>

This guide covers key concepts for using Zep effectively:

- [How Zep fits into your application](#how-zep-fits-into-your-application)
- [The Zep Knowledge Graph](#the-knowledge-graph)
- [User vs Group graphs](#user-vs-group-graphs)
- [Managing changes in facts over time](#managing-changes-in-facts-over-time)
- [Business data vs Chat Message data](#business-data-vs-chat-message-data)
- [Users and Chat Sessions](#users-and-chat-sessions)
- [Adding Memory](#adding-memory)
- [Retrieving memory](#retrieving-memory)
- [Improving Fact Quality](#improving-fact-quality)
- [Using Zep as an agentic tool](#using-zep-as-an-agentic-tool)
- [Other Zep Features](#other-zep-features)

## How Zep fits into your application

Your application sends Zep messages and other interactions your agent has with a human. Zep can also ingest data from your business sources in JSON, text, or chat message format. These sources may include CRM applications, emails, billing data, or conversations on other communication platforms like Slack.

<Frame>
 <img src="file:a7eead01-0816-4732-84b7-116b5f35c395" />
</Frame>

Zep fuses this data together on a knowledge graph, building a holistic view of the user's world and the relationships between entities. Zep offers a number of APIs for [adding and retrieving memory](#retrieving-memory). In addition to populating a prompt with Zep's memory, Zep's search APIs can be used to build [agentic tools](#using-zep-as-an-agentic-tool).

The example below shows Zep's `memory.context` field resulting from a call to `memory.get()`. This is an opinionated, easy to use context string that can be added to your prompt and contains facts and graph entities relevant to the current conversation with a user. For more about the temporal context of facts, see [Managing changes in facts over time](#managing-changes-in-facts-over-time).

Zep also returns a number of other artifacts in the `memory.get()` response, including raw `facts` objects. Zep's search methods can also be used to retrieve nodes, edges, and facts.

### Memory Context
Memory context is a string containing relevant facts and entities for the session. It is always present in the result of `memory.get()` 
call and can be optionally [received with the response of `memory.add()` call](/docs/performance/performance-best-practices#get-the-memory-context-string-sooner). 
<Tab title="Python" group-key="python" id="memory-context">
```python
# pass in the session ID of the conversation thread
memory = zep_client.memory.get(session_id="session_id") 
print(memory.context)
```
```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges

# format: FACT (Date range: from - to)

<FACTS>
  - Emily is experiencing issues with logging in. (2024-11-14 02:13:19+00:00 -
    present) 
  - User account Emily0e62 has a suspended status due to payment failure. 
    (2024-11-14 02:03:58+00:00 - present) 
  - user has the id of Emily0e62 (2024-11-14 02:03:54 - present)
  - The failed transaction used a card with last four digits 1234. (2024-09-15
    00:00:00+00:00 - present)
  - The reason for the transaction failure was 'Card expired'. (2024-09-15
    00:00:00+00:00 - present)
  - user has the name of Emily Painter (2024-11-14 02:03:54 - present) 
  - Account Emily0e62 made a failed transaction of 99.99. (2024-07-30 
    00:00:00+00:00 - 2024-08-30 00:00:00+00:00)
</FACTS>

# These are the most relevant entities

# ENTITY_NAME: entity summary

<ENTITIES>
  - Emily0e62: Emily0e62 is a user account associated with a transaction,
    currently suspended due to payment failure, and is also experiencing issues
    with logging in. 
  - Card expired: The node represents the reason for the transaction failure, 
    which is indicated as 'Card expired'. 
  - Magic Pen Tool: The tool being used by the user that is malfunctioning. 
  - User: user 
  - Support Agent: Support agent responding to the user's bug report. 
  - SupportBot: SupportBot is the virtual assistant providing support to the user, 
    Emily, identified as SupportBot. 
  - Emily Painter: Emily is a user reporting a bug with the magic pen tool, 
    similar to Emily Painter, who is expressing frustration with the AI art
    generation tool and seeking assistance regarding issues with the PaintWiz app.
</ENTITIES>
```
</Tab>

You can then include this context in your system prompt:

| MessageType | Content                                                                                                    |
| ----------- | ---------------------------------------------------------------------------------------------------------- |
| `System`    | Your system prompt <br /> <br /> `{Zep context string}`                                                               |
| `Assistant` | An assistant message stored in Zep                                                                         |
| `User`      | A user message stored in Zep                                                                               |
| ...         | ...                                                                                                        |
| `User`      | The latest user message                                                                                    |



## The Knowledge Graph

<Card title="What is a Knowledge Graph?" icon="duotone chart-network">
  A knowledge graph is a network of interconnected facts, such as *"Kendra loves
  Adidas shoes."* Each fact is a *"triplet"* represented by two entities, or
  nodes (*"Kendra", "Adidas shoes"*), and their relationship, or edge
  (*"loves"*).
  <br />
  Knowledge Graphs have been explored extensively for information retrieval.
  What makes Zep unique is its ability to autonomously build a knowledge graph
  while handling changing relationships and maintaining historical context.
</Card>

Zep automatically constructs a knowledge graph for each of your users. The knowledge graph contains entities, relationships, and facts related to your user, while automatically handling changing relationships and facts.

Here's an example of how Zep might extract graph data from a chat message, and then update the graph once new information is available:

![graphiti intro slides](file:f9ceebdb-fed6-45a0-9ff3-48c27535364c)

Each node and edge contains certain attributes - notably, a fact is always stored as an edge attribute. There are also datetime attributes for when the fact becomes [valid and when it becomes invalid](#managing-changes-in-facts-over-time).

## User vs Group graphs

Zep automatically creates a knowledge graph for each User of your application. You as the developer can also create a ["group graph"](/groups) (which is best thought of as an "arbitrary graph") for memory to be used by a group of Users, or for a more complicated use case.

For example, you could create a group graph for your company's product information or even messages related to a group chat. This avoids having to add the same data to each user graph. To do so, you'd use the `graph.add()` and `graph.search()` methods (see [Retrieving memory](#retrieving-memory)).

Group knowledge is not retrieved via the `memory.get()` method and is not included in the `memory.context` string. To use user and group graphs simultaneously, you need to add group-specific context to your prompt alongside the `memory.context` string.

Read more about groups [here](/groups).
## Managing changes in facts over time

When incorporating new data, Zep looks for existing nodes and edges in graph and decides whether to add new nodes/edges or to update existing ones. An update could mean updating an edge (for example, indicating the previous fact is no longer valid). 

For example, in the [animation above](#the-knowledge-graph), Kendra initially loves Adidas shoes. She later is angry that the shoes broke and states a preference for Puma shoes. As a result, Zep invalidates the fact that Kendra loves Adidas shoes and creates two new facts: "Kendra's Adidas shoes broke" and "Kendra likes Puma shoes".

Zep also looks for dates in all ingested data, such as the timestamp on a chat message or an article's publication date, informing how Zep sets the following edge attributes. This assists your agent in reasoning with time.

| Edge attribute           | Example                                             |
| :------------------ | :-------------------------------------------------- |
| **created_at**      | The time Zep learned that the user got married           |
| **valid_at**        | The time the user got married                       |
| **invalid_at**      | The time the user got divorced                      |
| **expired_at**      | The time Zep learned that the user got divorced          |



The `valid_at` and `invalid_at` attributes for each fact are then included in the `memory.context` string which is given to your agent:

```text
# format: FACT (Date range: from - to)
User account Emily0e62 has a suspended status due to payment failure. (2024-11-14 02:03:58+00:00 - present)
```

## Business data vs Chat Message data

Zep can ingest either unstructured text (e.g. documents, articles, chat messages) or JSON data (e.g. business data, or any other form of structured data). Conversational data is ingested through `memory.add()` in structured chat message format, and all other data is ingested through the `graph.add()` method.

## Users and Chat Sessions

A Session is a series of chat messages (e.g., between a user and your agent). [Users](/users) may have multiple Sessions.

Entities, relationships, and facts are extracted from the messages in a Session and added to the user's knowledge graph. All of a user's Sessions contribute to a single, shared knowledge graph for that user. Read more about sessions [here](/sessions).

<Note>
`SessionIDs` are arbitrary identifiers that you can map to relevant business objects in your app, such as users or a
conversation a user might have with your app.
</Note>

For code examples of how to create users and sessions, see the [Quickstart Guide](/quickstart#create-a-user-and-session).

## Adding Memory

There are two ways to add data to Zep: `memory.add()` and `graph.add()`.

### Using `memory.add()`

Add your chat history to Zep using the `memory.add()` method. `memory.add` is session-specific and expects data in chat message format, including a `role` name (e.g., user's real name), `role_type` (AI, human, tool), and message `content`. Zep stores the chat history and builds a user-level knowledge graph from the messages.

For code examples of how to add messages to Zep's memory, see the [Quickstart Guide](/quickstart#adding-messages-and-retrieving-context).

<Tip>
For best results, add chat history to Zep on every chat turn. That is, add both the AI and human messages in a single operation and in the order that the messages were created.
</Tip>

Additionally, for latency-sensitive applications, you can request the memory context directly in the response to the `memory.add` call. Read more [here](/docs/performance/performance-best-practices#get-the-memory-context-string-sooner).

### Using `graph.add()`

The `graph.add()` method enables you to add business data as a JSON object or unstructured text. It also supports adding data to Group graphs by passing in a `group_id` as opposed to a `user_id`.

For code examples of how to add business data to the graph, see the [Quickstart Guide](/quickstart#adding-business-data-to-a-graph).

## Retrieving memory

There are three ways to retrieve memory from Zep: `memory.get()`, `graph.search()`, and methods for retrieving specific nodes, edges, or episodes using UUIDs.

### Using `memory.get()`

The `memory.get()` method is a user-friendly, high-level API for retrieving relevant context from Zep. It uses the latest messages of the *given session* to determine what information is most relevant from the user's knowledge graph and returns that information in a [context string](#memory-context) for your prompt. Note that although `memory.get()` only requires a session ID, it is able to return memory derived from any session of that user. The session is just used to determine what's relevant.

`memory.get` also returns recent chat messages and raw facts that may provide additional context for your agent. It is user and session-specific and cannot retrieve data from group graphs.

For code examples of how to retrieve memory context for a session, see the [Quickstart Guide](/quickstart#retrieving-context-with-memoryget).

### Using `graph.search()`

The `graph.search()` method lets you search the graph directly, returning raw edges and/or nodes (defaults to edges), as opposed to facts. You can customize search parameters, such as the reranker used. For more on how search works, visit the [Graph Search](/searching-the-graph) guide. This method works for both User and Group graphs.

For code examples of how to search the graph, see the [Quickstart Guide](/quickstart#searching-the-graph).

### Retrieving specific nodes, edges, and episodes

Zep offers several utility methods for retrieving specific nodes, edges, or episodes by UUID, or all elements for a user or group. To retrieve a fact, you just need to retrieve its edge, since a fact is always the attribute of some edge. See the [Graph SDK reference](/sdk-reference/graph) for more.

## Improving Fact Quality

By using Zep's fact rating feature, you can make Zep automatically assign a rating to every fact using your own custom rating instruction. Then, when retrieving memory, you can set a minimum rating threshold so that the memory only contains the highest quality facts for your use case. Read more [here](/facts#rating-facts-for-relevancy).

## Using Zep as an agentic tool

Zep's memory retrieval methods can be used as agentic tools, enabling your agent to query Zep for relevant information. This allows your agent to access the user's knowledge graph and retrieve facts, entities, and relationships that are relevant to the current conversation.

For a complete code example of how to use Zep as an agentic tool, see the [Quickstart Guide](/quickstart#using-zep-as-an-agentic-tool).

## Other Zep Features

Additionally, Zep builds on Zep's memory layer with tools to help you build more deterministic and accurate applications:

- [Dialog Classification](/dialog-classification) is a flexible low-latency API for understanding intent, segmenting users, determining the state of a conversation and more, allowing you to select appropriate prompts and models, and manage application flow.
- [Structured Data Extraction](/structured-data-extraction) extracts data from conversations with high-fidelity and low-latency, enabling you to confidently populate your data store, call third-party applications, and build custom workflows.

---
title: Quickstart
subtitle: Get up and running with Zep in minutes
slug: quickstart
---

<Tip>
Looking for a more in-depth understanding? Check out our [Key Concepts](/concepts) page.
</Tip>

This quickstart guide will help you get up and running with Zep quickly. We will:
- Obtain an API key
- Install the SDK
- Initialize the client
- Create a user and session
- Add and retrieve messages
- View your knowledge graph
- Add business data to a user or group graph
- Search for edges or nodes in the graph


<Note>
Migrating from Mem0? Check out our [Mem0 Migration](/mem0-to-zep) guide.
</Note>


## Obtain an API Key

[Create a free Zep account](https://app.getzep.com/) and you will be prompted to create an API key.

## Install the SDK

### Python

Set up your Python project, ideally with [a virtual environment](https://medium.com/@vkmauryavk/managing-python-virtual-environments-with-uv-a-comprehensive-guide-ac74d3ad8dff), and then:

<Tabs>

<Tab title="pip">

```Bash
pip install zep-cloud
```

</Tab>
<Tab title="uv">

```Bash
uv pip install zep-cloud
```

</Tab>
</Tabs>

### TypeScript
Set up your TypeScript project and then:
<Tabs>

<Tab title="npm">

```Bash
npm install @getzep/zep-cloud
```

</Tab>
<Tab title="yarn">

```Bash
yarn add @getzep/zep-cloud
```

</Tab>
<Tab title="pnpm">

```Bash
pnpm install @getzep/zep-cloud
```

</Tab>
</Tabs>

### Go
Set up your Go project and then:
```Bash
go get github.com/getzep/zep-go/v2
```

## Initialize the Client

First, make sure you have a [.env file](https://metaschool.so/articles/what-are-env-files) with your API key:

```
ZEP_API_KEY=your_api_key_here
```

After creating your .env file, you'll need to source it in your terminal session:

```bash
source .env
```

Then, initialize the client with your API key:

<CodeBlocks>

```python Python
import os
from zep_cloud.client import Zep

API_KEY = os.environ.get('ZEP_API_KEY')

client = Zep(
    api_key=API_KEY,
)
```

```typescript TypeScript
import { ZepClient } from "@getzep/zep-cloud";

const API_KEY = process.env.ZEP_API_KEY;

const client = new ZepClient({
  apiKey: API_KEY,
});
```

```go Go
import (
    "github.com/getzep/zep-go/v2"
    zepclient "github.com/getzep/zep-go/v2/client"
    "github.com/getzep/zep-go/v2/option"
    "log"
)

client := zepclient.NewClient(
    option.WithAPIKey(os.Getenv("ZEP_API_KEY")),
)
```

</CodeBlocks>

<Info>
**The Python SDK Supports Async Use**

The Python SDK supports both synchronous and asynchronous usage. For async operations, import `AsyncZep` instead of `Zep` and remember to `await` client calls in your async code.
</Info>

## Create a User and Session

Before adding messages, you need to create a user and a session. A session is a chat thread - a container for messages between a user and an assistant. A user can have multiple sessions (different conversation threads).

<Note>
While messages are stored in sessions, the knowledge extracted from these messages is stored at the user level. This means that facts and entities learned in one session are available across all of the user's sessions. When you use `memory.get()`, Zep returns the most relevant memory from the user's entire knowledge graph, not just from the current session.
</Note>

### Create a User

<Warning>
It is important to provide at least the first name and ideally the last name of the user when calling `user.add`. Otherwise, Zep may not be able to correctly associate the user with references to the user in the data you add. If you don't have this information at the time the user is created, you can add it later with our [update user](/sdk-reference/user/update) method.
</Warning>

<CodeBlocks>

```python Python
# Create a new user
user_id = "user123"
new_user = client.user.add(
    user_id=user_id,
    email="user@example.com",
    first_name="Jane",
    last_name="Smith",
)
```

```typescript TypeScript
// Create a new user
const userId = "user123";
const user = await client.user.add({
  userId: userId,
  email: "user@example.com",
  firstName: "Jane",
  lastName: "Smith",
});
```

```go Go
import (
    "context"
    v2 "github.com/getzep/zep-go/v2"
)

// Create a new user
userId := "user123"
email := "user@example.com"
firstName := "Jane"
lastName := "Smith"
user, err := client.User.Add(context.TODO(), &v2.CreateUserRequest{
    UserID:    &userId,
    Email:     &email,
    FirstName: &firstName,
    LastName:  &lastName,
})
if err != nil {
    log.Fatal("Error creating user:", err)
}
fmt.Println("User created:", user)
```

</CodeBlocks>

### Create a Session

<CodeBlocks>

```python Python
import uuid

# Generate a unique session ID
session_id = uuid.uuid4().hex

# Create a new session for the user
client.memory.add_session(
    session_id=session_id,
    user_id=user_id,
)
```

```typescript TypeScript
import { v4 as uuid } from "uuid";

// Generate a unique session ID
const sessionId = uuid();

// Create a new session for the user
await client.memory.addSession({
  sessionId: sessionId,
  userId: userId,
});
```

```go Go
import (
    "context"
    "github.com/google/uuid"
    "github.com/getzep/zep-go/v2/models"
)

// Generate a unique session ID
sessionId := uuid.New().String()

// Create a new session for the user
session, err := client.Memory.AddSession(context.TODO(), &v2.CreateSessionRequest{
    SessionID: sessionId,
    UserID:    userId,
})
if err != nil {
    log.Fatal("Error creating session:", err)
}
fmt.Println("Session created:", session)
```

</CodeBlocks>


## Add Messages with memory.add

Add chat messages to a session using the `memory.add` method. These messages will be stored in the session history and used to build the user's knowledge graph.

<Warning>
It is important to provide the name of the user in the role field if possible, to help with graph construction. It's also helpful to provide a meaningful name for the assistant in its role field.
</Warning>

<CodeBlocks>

```python Python
# Define messages to add
from zep_cloud.types import Message

messages = [
    Message(
        role="Jane",
        content="Hi, my name is Jane Smith and I work at Acme Corp.",
        role_type="user",
    ),
    Message(
        role="AI Assistant",
        content="Hello Jane! Nice to meet you. How can I help you with Acme Corp today?",
        role_type="assistant",
    )
]

# Add messages to the session
client.memory.add(session_id, messages=messages)
```

```typescript TypeScript
// Define messages to add
import type { Message } from "@getzep/zep-cloud/api";

const messages: Message[] = [
  {
    role: "Jane",
    content: "Hi, my name is Jane Smith and I work at Acme Corp.",
    roleType: "user",
  },
  {
    role: "AI Assistant",
    content: "Hello Jane! Nice to meet you. How can I help you with Acme Corp today?",
    roleType: "assistant",
  }
];

// Add messages to the session
await client.memory.add(sessionId, { messages });
```

```go Go
import (
    "context"
    "github.com/getzep/zep-go/v2/models"
)

// Define messages to add
userRole := "Jane"
assistantRole := "AI Assistant"
messages := []*v2.Message{
    {
        Role:     &userRole,
        Content:  "Hi, my name is Jane Smith and I work at Acme Corp.",
        RoleType: "user",
    },
    {
        Role:     &assistantRole,
        Content:  "Hello Jane! Nice to meet you. How can I help you with Acme Corp today?",
        RoleType: "assistant",
    },
}

// Add messages to the session
_, err = client.Memory.Add(
    context.TODO(),
    sessionId,
    &v2.AddMemoryRequest{
        Messages: messages,
    },
)
if err != nil {
    log.Fatal("Error adding messages:", err)
}
```

</CodeBlocks>



## Retrieve Context with memory.get

Use the `memory.get` method to retrieve relevant context for a session. This includes a context string with facts and entities and recent messages that can be used in your prompt.

<CodeBlocks>

```python Python
# Get memory for the session
memory = client.memory.get(session_id=session_id)

# Access the context string (for use in prompts)
context_string = memory.context
print(context_string)

# Access recent messages
recent_messages = memory.messages
for msg in recent_messages:
    print(f"{msg.role}: {msg.content}")
```

```typescript TypeScript
// Get memory for the session
const memory = await client.memory.get(sessionId);

// Access the context string (for use in prompts)
const contextString = memory.context;
console.log(contextString);

// Access recent messages
if (memory.messages) {
  memory.messages.forEach(msg => {
    console.log(`${msg.role}: ${msg.content}`);
  });
}
```

```go Go
import (
    "context"
    "fmt"
)

// Get memory for the session
memory, err := client.Memory.Get(context.TODO(), sessionId, nil)
if err != nil {
    log.Fatal("Error getting memory:", err)
}

// Access the context string (for use in prompts)
contextString := memory.Context
fmt.Println(contextString)

// Access recent messages
recentMessages := memory.Messages
for _, msg := range recentMessages {
    fmt.Printf("%s: %s\n", *msg.Role, msg.Content)
}
```

</CodeBlocks>

## View your Knowledge Graph
Since you've created memory, you can view your knowledge graph by navigating to [the Zep Dashboard](https://app.getzep.com/), then Users > "user123" > View Graph. You can also click the "View Episodes" button to see when data is finished being added to the knowledge graph.

## Add Business Data to a Graph

You can add business data directly to a user's graph or to a group graph using the `graph.add` method. This data can be in the form of messages, text, or JSON.

<CodeBlocks>

```python Python
# Add text data to a user's graph
new_episode = client.graph.add(
    user_id=user_id,
    type="text",
    data="Jane Smith is a senior software engineer who has been with Acme Corp for 5 years."
)
print("New episode created:", new_episode)
# Add JSON data to a user's graph
import json
json_data = {
    "employee": {
        "name": "Jane Smith",
        "position": "Senior Software Engineer",
        "department": "Engineering",
        "projects": ["Project Alpha", "Project Beta"]
    }
}
client.graph.add(
    user_id=user_id,
    type="json",
    data=json.dumps(json_data)
)

# Add data to a group graph (shared across users)
group_id = "engineering_team"
client.graph.add(
    group_id=group_id,
    type="text",
    data="The engineering team is working on Project Alpha and Project Beta."
)
```

```typescript TypeScript
// Add text data to a user's graph
const newEpisode = await client.graph.add({
  userId: userId,
  type: "text",
  data: "Jane Smith is a senior software engineer who has been with Acme Corp for 5 years."
});
console.log("New episode created:", newEpisode);
// Add JSON data to a user's graph
const jsonData = {
  employee: {
    name: "Jane Smith",
    position: "Senior Software Engineer",
    department: "Engineering",
    projects: ["Project Alpha", "Project Beta"]
  }
};
await client.graph.add({
  userId: userId,
  type: "json",
  data: JSON.stringify(jsonData)
});

// Add data to a group graph (shared across users)
const groupId = "engineering_team";
await client.graph.add({
  groupId: groupId,
  type: "text",
  data: "The engineering team is working on Project Alpha and Project Beta."
});
```

```go Go
import (
    "context"
    "encoding/json"
    "github.com/getzep/zep-go/v2/models"
)

// Add text data to a user's graph
data := "Jane Smith is a senior software engineer who has been with Acme Corp for 5 years."
newEpisode, err := client.Graph.Add(context.TODO(), &v2.AddDataRequest{
    UserID: &userId,
    Type:   v2.GraphDataTypeText.Ptr(),
    Data:   &data,
})
if err != nil {
    log.Fatal("Error adding text data:", err)
}
fmt.Println("New episode added:", newEpisode)

// Add JSON data to a user's graph
type Employee struct {
    Name       string   `json:"name"`
    Position   string   `json:"position"`
    Department string   `json:"department"`
    Projects   []string `json:"projects"`
}
jsonData := map[string]Employee{
    "employee": {
        Name:       "Jane Smith",
        Position:   "Senior Software Engineer",
        Department: "Engineering",
        Projects:   []string{"Project Alpha", "Project Beta"},
    },
}
jsonBytes, err := json.Marshal(jsonData)
if err != nil {
    log.Fatal("Error marshaling JSON data:", err)
}
jsonString := string(jsonBytes)
_, err = client.Graph.Add(context.TODO(), &v2.AddDataRequest{
    UserID: &userId,
    Type:   v2.GraphDataTypeJSON.Ptr(),
    Data:   &jsonString,
})
if err != nil {
    log.Fatal("Error adding JSON data:", err)
}

// Add data to a group graph (shared across users)
groupId := "engineering_team"
groupData := "The engineering team is working on Project Alpha and Project Beta."
_, err = client.Graph.Add(context.TODO(), &v2.AddDataRequest{
    GroupID: &groupId,
    Type:    v2.GraphDataTypeText.Ptr(),
    Data:    &groupData,
})
if err != nil {
    log.Fatal("Error adding group data:", err)
}

```

</CodeBlocks>

## Search the Graph

Use the `graph.search` method to search for edges or nodes in the graph. This is useful for finding specific information about a user or group.

<CodeBlocks>

```python Python
# Search for edges in a user's graph
edge_results = client.graph.search(
    user_id=user_id,
    query="What projects is Jane working on?",
    scope="edges",  # Default is "edges"
    limit=5
)

# Search for nodes in a user's graph
node_results = client.graph.search(
    user_id=user_id,
    query="Jane Smith",
    scope="nodes",
    limit=5
)

# Search in a group graph
group_results = client.graph.search(
    group_id=group_id,
    query="Project Alpha",
    scope="edges",
    limit=5
)
```

```typescript TypeScript
// Search for edges in a user's graph
const edgeResults = await client.graph.search({
  userId: userId,
  query: "What projects is Jane working on?",
  scope: "edges",  // Default is "edges"
  limit: 5
});

// Search for nodes in a user's graph
const nodeResults = await client.graph.search({
  userId: userId,
  query: "Jane Smith",
  scope: "nodes",
  limit: 5
});

// Search in a group graph
const groupResults = await client.graph.search({
  groupId: groupId,
  query: "Project Alpha",
  scope: "edges",
  limit: 5
});
```

```go Go
import (
    "context"
    "github.com/getzep/zep-go/v2/models"
)

// Search for edges in a user's graph
limit := 5
edgeResults, err := client.Graph.Search(context.TODO(), &v2.GraphSearchQuery{
    UserID: &userId,
    Query:  "What projects is Jane working on?",
    Scope:  v2.GraphSearchScopeEdges.Ptr(),
    Limit:  &limit,
})
if err != nil {
    log.Fatal("Error searching graph:", err)
}
fmt.Println("Edge search results:", edgeResults)

// Search for nodes in a user's graph
nodeResults, err := client.Graph.Search(context.TODO(), &v2.GraphSearchQuery{
    UserID: &userId,
    Query:  "Jane Smith",
    Scope:  v2.GraphSearchScopeNodes.Ptr(),
    Limit:  &limit,
})
if err != nil {
    log.Fatal("Error searching graph:", err)
}
fmt.Println("Node search results:", nodeResults)

// Search in a group graph
groupResults, err := client.Graph.Search(context.TODO(), &v2.GraphSearchQuery{
    GroupID: &groupId,
    Query:   "Project Alpha",
    Scope:   v2.GraphSearchScopeEdges.Ptr(),
    Limit:   &limit,
})
if err != nil {
    log.Fatal("Error searching graph:", err)
}
fmt.Println("Group search results:", groupResults)
```

</CodeBlocks>

## Use Zep as an Agentic Tool

Zep's memory retrieval methods can be used as agentic tools, enabling your agent to query Zep for relevant information. 
The example below shows how to create a LangChain LangGraph tool to search for facts in a user's graph.

<CodeBlocks>

```python Python
from zep_cloud.client import AsyncZep

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode

zep = AsyncZep(api_key=os.environ.get('ZEP_API_KEY'))

@tool
async def search_facts(state: MessagesState, query: str, limit: int = 5):
    """Search for facts in all conversations had with a user.
    
    Args:
        state (MessagesState): The Agent's state.
        query (str): The search query.
        limit (int): The number of results to return. Defaults to 5.
    Returns:
        list: A list of facts that match the search query.
    """
    search_results = await zep.graph.search(
      user_id=state['user_name'], 
      query=query, 
      limit=limit, 
    )

    return [edge.fact for edge in search_results.edges]

tools = [search_facts]
tool_node = ToolNode(tools)
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0).bind_tools(tools)
```

</CodeBlocks>

## Next Steps

Now that you've learned the basics of using Zep, you can:

- Learn more about [Key Concepts](/concepts)
- Explore the [Graph API](/adding-data-to-the-graph) for adding and retrieving data
- Understand [Users and Sessions](/users) in more detail
- Learn about [Memory Context](/concepts#memory-context) for building better prompts
- Explore [Graph Search](/searching-the-graph) for advanced search capabilities

---
title: Building a Chatbot with Zep
subtitle: >-
  Familiarize yourself with Zep and the Zep SDKs, culminating in building a
  simple chatbot.
slug: walkthrough
---

<Tip>
For an introduction to Zep's memory layer, Knowledge Graph, and other key concepts, see the [Concepts Guide](/concepts).
</Tip>

<Note>
A Jupyter notebook version of this guide is [available here](https://github.com/getzep/zep-python/blob/main/examples/quickstart/quickstart.ipynb).
</Note>

In this guide, we'll walk through a simple example of how to use Zep Cloud to build a chatbot. We're going to upload a number of datasets to Zep, building a graph of data about a user.

Then we'll use the Zep Python SDK to retrieve and search the data.

Finally, we'll build a simple chatbot that uses Zep to retrieve and search data to respond to a user.

## Set up your environment

1. Sign up for a [Zep Cloud](https://www.getzep.com/) account.

2. Ensure you install required dependencies into your Python environment before running this notebook. See [Installing Zep SDKs](sdks.mdx) for more information. Optionally create your environment in a `virtualenv`.

```bash
pip install zep-cloud openai rich python-dotenv
```

3. Ensure that you have a `.env` file in your working directory that includes your `ZEP_API_KEY` and `OPENAI_API_KEY`:

<Note>
  Zep API keys are specific to a project. You can create multiple keys for a
  single project. Visit `Project Settings` in the Zep dashboard to manage your
  API keys.
</Note>

```text
ZEP_API_KEY=<key>
OPENAI_API_KEY=<key>
```

<Tabs group="imports-and-client">

<Tab title="Python" group-key="python">
```python
import os
import json
import uuid

from openai import OpenAI
import rich

from dotenv import load_dotenv
from zep_cloud.client import Zep
from zep_cloud import Message

load_dotenv()

zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))

oai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)
```
</Tab>

<Tab title="Typescript" group-key="ts">
```typescript
import { ZepClient } from "@getzep/zep-cloud";
import * as dotenv from "dotenv";
import { v4 as uuidv4 } from 'uuid';
import OpenAI from 'openai';

dotenv.config();

const zep = new ZepClient({ apiKey: process.env.ZEP_API_KEY });

const oai_client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});
```
</Tab>

</Tabs>

<Info>We also provide an [Asynchronous Python client](/sdks#initialize-client).</Info>

## Create User and add a Session

Users in Zep may have one or more chat sessions. These are threads of messages between the user and an agent.

<Tip>
  Include the user's **full name** and **email address** when creating a user.
  This improves Zep's ability to associate data, such as emails or documents,
  with a user.
</Tip>

<Tabs group="create-user">
<Tab title="Python" group-key="python">
```python
bot_name = "SupportBot"
user_name = "Emily"
user_id = user_name + str(uuid.uuid4())[:4]
session_id = str(uuid.uuid4())

zep.user.add(
    user_id=user_id,
    email=f"{user_name}@painters.com",
    first_name=user_name,
    last_name="Painter",
)

zep.memory.add_session(
    user_id=user_id,
    session_id=session_id,
)
```
</Tab>

<Tab title="Typescript" group-key="ts">
```typescript
const bot_name = "SupportBot";
const user_name = "Emily";
const user_id = user_name + uuidv4().substring(0, 4);
const session_id = uuidv4();

await zep.user.add({
  userId: user_id,
  email: `${user_name}@painters.com`,
  firstName: user_name,
  lastName: "Painter",
});

await zep.memory.addSession({
  userId: user_id,
  sessionId: session_id,
});
```
</Tab>
</Tabs>

## Datasets

We're going to use the [memory](/concepts#using-memoryadd) and [graph](/adding-data-to-the-graph) APIs to upload an assortment of data to Zep. These include past dialog with the agent, CRM support cases, and billing data.

<Tabs group="datasets">
<Tab title="Python" group-key="python">
```python
support_cases = [
    {
        "subject": "Bug: Magic Pen Tool Drawing Goats Instead of Boats",
        "messages": [
            {
                "role": "user",
                "content": "Whenever I use the magic pen tool to draw boats, it ends up drawing goats instead.",
                "timestamp": "2024-03-16T14:20:00Z",
            },
            {
                "role": "support_agent",
                "content": f"Hi {user_name}, that sounds like a bug! Thanks for reporting it. Could you let me know exactly how you're using the tool when this happens?",
                "timestamp": "2024-03-16T14:22:00Z",
            },
            {
                "role": "user",
                "content": "Sure, I select the magic pen, draw a boat shape, and it just replaces the shape with goats.",
                "timestamp": "2024-03-16T14:25:00Z",
            },
            {
                "role": "support_agent",
                "content": "Got it! We'll escalate this to our engineering team. In the meantime, you can manually select the boat shape from the options rather than drawing it with the pen.",
                "timestamp": "2024-03-16T14:27:00Z",
            },
            {
                "role": "user",
                "content": "Okay, thanks. I hope it gets fixed soon!",
                "timestamp": "2024-03-16T14:30:00Z",
            },
        ],
        "status": "escalated",
    },
]

chat_history = [
    {
        "role": "assistant",
        "name": bot_name,
        "content": f"Hello {user_name}, welcome to PaintWiz support. How can I assist you today?",
        "timestamp": "2024-03-15T10:00:00Z",
    },
    {
        "role": "user",
        "name": user_name,
        "content": "I'm absolutely furious! Your AI art generation is completely broken!",
        "timestamp": "2024-03-15T10:02:00Z",
    },
    {
        "role": "assistant",
        "name": bot_name,
        "content": f"I'm sorry to hear that you're experiencing issues, {user_name}. Can you please provide more details about what's going wrong?",
        "timestamp": "2024-03-15T10:03:00Z",
    },
    {
        "role": "user",
        "name": user_name,
        "content": "Every time I try to draw mountains, your stupid app keeps turning them into fountains! And what's worse, all the people in my drawings have six fingers! It's ridiculous!",
        "timestamp": "2024-03-15T10:05:00Z",
    },
    {
        "role": "assistant",
        "name": bot_name,
        "content": f"I sincerely apologize for the frustration this is causing you, {user_name}. That certainly sounds like a significant glitch in our system. I understand how disruptive this can be to your artistic process. Can you tell me which specific tool or feature you're using when this occurs?",
        "timestamp": "2024-03-15T10:06:00Z",
    },
    {
        "role": "user",
        "name": user_name,
        "content": "I'm using the landscape generator and the character creator. Both are completely messed up. How could you let this happen?",
        "timestamp": "2024-03-15T10:08:00Z",
    },
]

transactions = [
    {
        "date": "2024-07-30",
        "amount": 99.99,
        "status": "Success",
        "account_id": user_id,
        "card_last_four": "1234",
    },
    {
        "date": "2024-08-30",
        "amount": 99.99,
        "status": "Failed",
        "account_id": user_id,
        "card_last_four": "1234",
        "failure_reason": "Card expired",
    },
    {
        "date": "2024-09-15",
        "amount": 99.99,
        "status": "Failed",
        "account_id": user_id,
        "card_last_four": "1234",
        "failure_reason": "Card expired",
    },
]

account_status = {
    "user_id": user_id,
    "account": {
        "account_id": user_id,
        "account_status": {
            "status": "suspended",
            "reason": "payment failure",
        },
    },
}

def convert_to_zep_messages(chat_history: list[dict[str, str | None]]) -> list[Message]:
    """
    Convert chat history to Zep messages.

    Args:
    chat_history (list): List of dictionaries containing chat messages.

    Returns:
    list: List of Zep Message objects.
    """
    return [
        Message(
            role_type=msg["role"],
            role=msg.get("name", None),
            content=msg["content"],
        )
        for msg in chat_history
    ]

# Zep's high-level API allows us to add a list of messages to a session.
zep.memory.add(
    session_id=session_id, messages=convert_to_zep_messages(chat_history)
)

# The lower-level data API allows us to add arbitrary data to a user's Knowledge Graph.
for tx in transactions:
    zep.graph.add(user_id=user_id, data=json.dumps(tx), type="json")

    zep.graph.add(
        user_id=user_id, data=json.dumps(account_status), type="json"
    )

for case in support_cases:
    zep.graph.add(user_id=user_id, data=json.dumps(case), type="json")
```
</Tab>

<Tab title="Typescript" group-key="ts">
```typescript
const support_cases = [
  {
    subject: "Bug: Magic Pen Tool Drawing Goats Instead of Boats",
    messages: [
      {
        role: "user",
        content: "Whenever I use the magic pen tool to draw boats, it ends up drawing goats instead.",
        timestamp: "2024-03-16T14:20:00Z",
      },
      {
        role: "support_agent",
        content: `Hi ${user_name}, that sounds like a bug! Thanks for reporting it. Could you let me know exactly how you're using the tool when this happens?`,
        timestamp: "2024-03-16T14:22:00Z",
      },
      {
        role: "user",
        content: "Sure, I select the magic pen, draw a boat shape, and it just replaces the shape with goats.",
        timestamp: "2024-03-16T14:25:00Z",
      },
      {
        role: "support_agent",
        content: "Got it! We'll escalate this to our engineering team. In the meantime, you can manually select the boat shape from the options rather than drawing it with the pen.",
        timestamp: "2024-03-16T14:27:00Z",
      },
      {
        role: "user",
        content: "Okay, thanks. I hope it gets fixed soon!",
        timestamp: "2024-03-16T14:30:00Z",
      },
    ],
    status: "escalated",
  },
];

const chat_history = [
  {
    role: "assistant",
    name: bot_name,
    content: `Hello ${user_name}, welcome to PaintWiz support. How can I assist you today?`,
    timestamp: "2024-03-15T10:00:00Z",
  },
  {
    role: "user",
    name: user_name,
    content: "I'm absolutely furious! Your AI art generation is completely broken!",
    timestamp: "2024-03-15T10:02:00Z",
  },
  {
    role: "assistant",
    name: bot_name,
    content: `I'm sorry to hear that you're experiencing issues, ${user_name}. Can you please provide more details about what's going wrong?`,
    timestamp: "2024-03-15T10:03:00Z",
  },
  {
    role: "user",
    name: user_name,
    content: "Every time I try to draw mountains, your stupid app keeps turning them into fountains! And what's worse, all the people in my drawings have six fingers! It's ridiculous!",
    timestamp: "2024-03-15T10:05:00Z",
  },
  {
    role: "assistant",
    name: bot_name,
    content: `I sincerely apologize for the frustration this is causing you, ${user_name}. That certainly sounds like a significant glitch in our system. I understand how disruptive this can be to your artistic process. Can you tell me which specific tool or feature you're using when this occurs?`,
    timestamp: "2024-03-15T10:06:00Z",
  },
  {
    role: "user",
    name: user_name,
    content: "I'm using the landscape generator and the character creator. Both are completely messed up. How could you let this happen?",
    timestamp: "2024-03-15T10:08:00Z",
  },
];

const transactions = [
  {
    date: "2024-07-30",
    amount: 99.99,
    status: "Success",
    account_id: user_id,
    card_last_four: "1234",
  },
  {
    date: "2024-08-30",
    amount: 99.99,
    status: "Failed",
    account_id: user_id,
    card_last_four: "1234",
    failure_reason: "Card expired",
  },
  {
    date: "2024-09-15",
    amount: 99.99,
    status: "Failed",
    account_id: user_id,
    card_last_four: "1234",
    failure_reason: "Card expired",
  },
];

const account_status = {
  user_id: user_id,
  account: {
    account_id: user_id,
    account_status: {
      status: "suspended",
      reason: "payment failure",
    },
  },
};

/**
 * Convert chat history to Zep messages.
 * 
 * Args:
 * chatHistory (array): Array of objects containing chat messages.
 * 
 * Returns:
 * array: Array of Zep message objects.
 */
const convertToZepMessages = (chatHistory: any[]) => {
  return chatHistory.map(msg => ({
    roleType: msg.role,
    role: msg.name || null,
    content: msg.content,
  }));
};

// Zep's high-level API allows us to add a list of messages to a session.
await zep.memory.add(session_id, {
  messages: convertToZepMessages(chat_history)
});

// The lower-level data API allows us to add arbitrary data to a user's Knowledge Graph.
for (const tx of transactions) {
  await zep.graph.add({
    userId: user_id,
    type: "json",
    data: JSON.stringify(tx)
  });

  await zep.graph.add({
    userId: user_id,
    type: "json",
    data: JSON.stringify(account_status)
  });
}

for (const case_data of support_cases) {
  await zep.graph.add({
    userId: user_id,
    type: "json",
    data: JSON.stringify(case_data)
  });
}
```
</Tab>
</Tabs>

### Wait a minute or two!

<Tip>
  We've batch uploaded a number of datasets that need to be ingested into Zep's
  graph before they can be queried. In ordinary operation, this data would
  stream into Zep and ingestion latency would be negligible.
</Tip>

## Retrieve data from Zep

We'll start with getting a list of facts, which are stored on the edges of the graph. We'll see the temporal data associated with facts as well as the graph nodes the fact is related to.

<Tip>This data is also viewable in the Zep Web application.</Tip>

<Tabs group="retrieve-edges">
<Tab title="Python" group-key="python">
```python
all_user_edges = zep.graph.edge.get_by_user_id(user_id=user_id)
rich.print(all_user_edges[:3])
```
</Tab>
<Tab title="Typescript" group-key="ts">
```typescript
const all_user_edges = await zep.graph.edge.getByUserId(user_id);
console.log(all_user_edges.slice(0, 3));
```
</Tab>
</Tabs>

```text
[
    EntityEdge(
        created_at='2025-02-20T20:31:01.769332Z',
        episodes=['0d3a35c7-ebd3-427d-89a6-1a8dabd2df64'],
        expired_at='2025-02-20T20:31:18.742184Z',
        fact='The transaction failed because the card expired.',
        invalid_at='2024-09-15T00:00:00Z',
        name='HAS_FAILURE_REASON',
        source_node_uuid='06c61c00-9101-474f-9bca-42b4308ec378',
        target_node_uuid='07efd834-f07a-4c3c-9b32-d2fd9362afd5',
        uuid_='fb5ee0df-3aa0-44f3-889d-5bb163971b07',
        valid_at='2024-08-30T00:00:00Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:31:33.771557Z',
        episodes=['60d1d20e-ed6c-4966-b1da-3f4ca274a524'],
        expired_at=None,
        fact='Emily uses the magic pen tool to draw boats.',
        invalid_at=None,
        name='USES_TOOL',
        source_node_uuid='36f5c5c6-eb16-4ebb-9db0-fd34809482f5',
        target_node_uuid='e337522d-3a62-4c45-975d-904e1ba25667',
        uuid_='f9eb0a98-1624-4932-86ca-be75a3c248e5',
        valid_at='2025-02-20T20:29:40.217412Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:30:28.499178Z',
        episodes=['b8e4da4c-dd5e-4c48-bdbc-9e6568cd2d2e'],
        expired_at=None,
        fact="SupportBot understands how disruptive the glitch in the AI art generation can be to Emily's artistic process.",
        invalid_at=None,
        name='UNDERSTANDS',
        source_node_uuid='fd4ab1f0-e19e-40b7-aaec-78bd97571725',
        target_node_uuid='8e5686fc-f175-4da9-8778-ad8d60fc469a',
        uuid_='f8c52a21-e938-46a3-b930-04671d0c018a',
        valid_at='2025-02-20T20:29:39.08846Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    )
]
```

The high-level [memory API](/concepts#using-memoryget) provides an easy way to retrieve memory relevant to the current conversation by using the last 4 messages and their proximity to the User node.

<Tip>
  The `memory.get` method is a good starting point for retrieving relevant conversation context. It shortcuts passing recent messages to the `graph.search` API and returns a [context string](/concepts#memory-context), raw facts, and historical chat messages, providing everything needed for your agent's prompts.
</Tip>

<Tabs group="memory-get">
<Tab title="Python" group-key="python">
```python
memory = zep.memory.get(session_id=session_id)
rich.print(memory.context)
```
</Tab>
<Tab title="Typescript" group-key="ts">
```typescript
const memory = await zep.memory.get(session_id);
console.log(memory.context);
```
</Tab>
</Tabs>
```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
<FACTS>
  - SupportBot understands how disruptive the glitch in the AI art generation can be to Emily's artistic process. (2025-02-20 20:29:39 - present)
  - SupportBot sincerely apologizes to Emily for the frustration caused by the issues with the AI art generation. (2025-02-20 20:29:39 - present)
  - Emily has contacted SupportBot for assistance regarding issues she is experiencing. (2025-02-20 20:29:39 - present)
  - The user Emily reported a bug regarding the magic pen tool drawing goats instead of boats. (2024-03-16 14:20:00 - present)
  - The bug report has been escalated to the engineering team. (2024-03-16 14:27:00 - present)
  - Emily is a user of the AI art generation. (2025-02-20 20:29:39 - present)
  - user has the name of Emily Painter (2025-02-20 20:29:39 - present)
  - Emily5e57 is using the landscape generator. (2025-02-20 20:29:39 - 2025-02-20 20:29:39)
  - user has the id of Emily5e57 (2025-02-20 20:29:39 - present)
  - user has the email of Emily@painters.com (2025-02-20 20:29:39 - present)
  - Emily is furious about the stupid app. (2025-02-20 20:29:39 - present)
  - Emily claims that the AI art generation is completely broken. (2025-02-20 20:29:39 - present)
</FACTS>

# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
  - Emily Painter: Emily Painter contacted PaintWiz support for assistance, where she was welcomed by the support bot that inquired about the specific issues she was facing to provide better help.
  - Emily@painters.com: user with the email of Emily@painters.com
  - Emily5e57: Emily5e57, a user of the PaintWiz AI art generation tool, successfully processed a transaction of $99.99 on July 30, 2024, using a card ending in '1234'. However, she is experiencing
significant frustration with the application due to malfunctions, such as the landscape generator incorrectly transforming mountains into fountains and characters being depicted with six fingers. 
These issues have led her to question the reliability of the tool, and she considers it to be completely broken. Emily has reached out to PaintWiz support for assistance, as these problems are 
severely disrupting her artistic process.
  - PaintWiz support: PaintWiz is an AI art generation platform that provides tools for users to create art. Recently, a user named Emily reported significant issues with the service, claiming that
the AI art generation is not functioning properly. The support bot responded to her concerns, apologizing for the disruption to her artistic process and asking for more details about the specific 
tool or feature she was using. This interaction highlights PaintWiz's commitment to customer support, as they actively seek to assist users with their inquiries and problems related to their 
products.
  - SupportBot: A support agent named Emily addressed a user's report about a bug in a drawing application where the magic pen tool incorrectly produced goats instead of boats. After confirming the
issue, she escalated it to the engineering team and suggested a temporary workaround of manually selecting the boat shape. Meanwhile, SupportBot, a virtual assistant for PaintWiz, also assisted 
another user named Emily who was frustrated with the AI art generation feature, acknowledging her concerns and requesting more details to help resolve the problem.
  - AI art generation: Emily, a user, expressed her frustration regarding the AI art generation, stating that it is completely broken.
  - options: The user reported a bug with the magic pen tool, stating that when attempting to draw boats, the tool instead draws goats. The support agent acknowledged the issue and requested more 
details about how the user was utilizing the tool. The user explained that they select the magic pen and draw a boat shape, but it gets replaced with goats. The support agent confirmed they would 
escalate the issue to the engineering team and suggested that the user manually select the boat shape from the options instead of drawing it with the pen. The user expressed hope for a quick 
resolution.
</ENTITIES>
```

<Tabs group="memory-messages">
<Tab title="Python" group-key="python">
```python
rich.print(memory.messages)
```
</Tab>
<Tab title="Typescript" group-key="ts">
```typescript
console.log(memory.messages);
```
</Tab>
</Tabs>

```text
[
    Message(
        content='Hello Emily, welcome to PaintWiz support. How can I assist you today?',
        created_at='2025-02-20T20:29:39.08846Z',
        metadata=None,
        role='SupportBot',
        role_type='assistant',
        token_count=0,
        updated_at='0001-01-01T00:00:00Z',
        uuid_='e2b86f93-84d6-4270-adbc-e421f39b6f90'
    ),
    Message(
        content="I'm absolutely furious! Your AI art generation is completely broken!",
        created_at='2025-02-20T20:29:39.08846Z',
        metadata=None,
        role='Emily',
        role_type='user',
        token_count=0,
        updated_at='0001-01-01T00:00:00Z',
        uuid_='ec39e501-6dcc-4f8c-b300-f586d66005d8'
    )
]
```

We can also use the [graph API](/searching-the-graph) to search edges/facts for arbitrary text. This API offers more options, including the ability to search node summaries and various re-rankers.

<Tabs group="graph-search">
<Tab title="Python" group-key="python">
```python
r = zep.graph.search(user_id=user_id, query="Why are there so many goats?", limit=4, scope="edges")
rich.print(r.edges)
```
</Tab>
<Tab title="Typescript" group-key="ts">
```typescript
const r = await zep.graph.search({
  userId: user_id,
  query: "Why are there so many goats?",
  limit: 4,
  scope: "edges"
});
console.log(r.edges);
```
</Tab>
</Tabs>

```text
[
    EntityEdge(
        created_at='2025-02-20T20:31:33.771566Z',
        episodes=['60d1d20e-ed6c-4966-b1da-3f4ca274a524'],
        expired_at=None,
        fact='The magic pen tool draws goats instead of boats when used by Emily.',
        invalid_at=None,
        name='DRAWS_INSTEAD_OF',
        source_node_uuid='e337522d-3a62-4c45-975d-904e1ba25667',
        target_node_uuid='9814a57f-53a4-4d4a-ad5a-15331858ce18',
        uuid_='022687b6-ae08-4fef-9d6e-17afb07acdea',
        valid_at='2025-02-20T20:29:40.217412Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:31:33.771528Z',
        episodes=['60d1d20e-ed6c-4966-b1da-3f4ca274a524'],
        expired_at=None,
        fact='The user Emily reported a bug regarding the magic pen tool drawing goats instead of boats.',
        invalid_at=None,
        name='REPORTED_BY',
        source_node_uuid='36f5c5c6-eb16-4ebb-9db0-fd34809482f5',
        target_node_uuid='cff4e758-d1a4-4910-abe7-20101a1f0d77',
        uuid_='5c3124ec-b4a3-4564-a38f-02338e3db4c4',
        valid_at='2024-03-16T14:20:00Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:30:19.910797Z',
        episodes=['ff9eba8b-9e90-4765-a0ce-15eb44410f70'],
        expired_at=None,
        fact='The stupid app generates mountains.',
        invalid_at=None,
        name='GENERATES',
        source_node_uuid='b6e5a0ee-8823-4647-b536-5e6af0ba113a',
        target_node_uuid='43aaf7c9-628c-4bf0-b7cb-02d3e9c1a49c',
        uuid_='3514a3ad-1ed5-42c7-9f70-02834e8904bf',
        valid_at='2025-02-20T20:29:39.08846Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    ),
    EntityEdge(
        created_at='2025-02-20T20:30:19.910816Z',
        episodes=['ff9eba8b-9e90-4765-a0ce-15eb44410f70'],
        expired_at=None,
        fact='The stupid app keeps turning mountains into fountains.',
        invalid_at=None,
        name='TRANSFORMS_INTO',
        source_node_uuid='43aaf7c9-628c-4bf0-b7cb-02d3e9c1a49c',
        target_node_uuid='0c90b42c-2b9f-4998-aa67-cc968f9002d3',
        uuid_='2f113810-3597-47a4-93c5-96d8002366fa',
        valid_at='2025-02-20T20:29:39.08846Z',
        graph_id='8e5686fc-f175-4da9-8778-ad8d60fc469a'
    )
]
```

## Creating a simple Chatbot

In the next cells, Emily starts a new chat session with a support agent and complains that she can't log in. Our simple chatbot will, given relevant facts retrieved from Zep's graph, respond accordingly.

Here, the support agent is provided with Emily's billing information and account status, which Zep retrieves as most relevant to Emily's login issue.

<Tabs group="new-session">
<Tab title="Python" group-key="python">
```python
new_session_id = str(uuid.uuid4())

emily_message = "Hi, I can't log in!"

# We start a new session indicating that Emily has started a new chat with the support agent.
zep.memory.add_session(user_id=user_id, session_id=new_session_id)

# We need to add the Emily's message to the session in order for memory.get to return
# relevant facts related to the message
zep.memory.add(
    session_id=new_session_id,
    messages=[Message(role_type="user", role=user_name, content=emily_message)],
)
```
</Tab>

<Tab title="Typescript" group-key="ts">
```typescript
const new_session_id = uuidv4();
const emily_message = "Hi, I can't log in!";

// We start a new session indicating that Emily has started a new chat with the support agent.
await zep.memory.addSession({
  userId: user_id,
  sessionId: new_session_id
});

// We need to add the Emily's message to the session in order for memory.get to return
// relevant facts related to the message
await zep.memory.add(new_session_id, {
  messages: [{
    roleType: "user",
    role: user_name,
    content: emily_message
  }]
});
```
</Tab>
</Tabs>

<Tabs group="chatbot">
<Tab title="Python" group-key="python">
```python
system_message = """
You are a customer support agent. Carefully review the facts about the user below and respond to the user's question.
Be helpful and friendly.
"""

memory = zep.memory.get(session_id=new_session_id)

messages = [
    {
        "role": "system",
        "content": system_message,
    },
    {
        "role": "assistant",
        # The context field is an opinionated string that contains facts and entities relevant to the current conversation.
        "content": memory.context,
    },
    {
        "role": "user",
        "content": emily_message,
    },
]

response = oai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    temperature=0,
)

print(response.choices[0].message.content)
```
</Tab>
<Tab title="Typescript" group-key="ts">
```typescript
const system_message = `
You are a customer support agent. Carefully review the facts about the user below and respond to the user's question.
Be helpful and friendly.
`;

const new_memory = await zep.memory.get(new_session_id);

const messages = [
  {
    role: "system" as const,
    content: system_message,
  },
  {
    role: "assistant" as const,
    // The context field is an opinionated string that contains facts and entities relevant to the current conversation.
    content: new_memory.context || "",
  },
  {
    role: "user" as const,
    content: emily_message,
  },
];

const response = await oai_client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: messages,
  temperature: 0,
});

console.log(response.choices[0].message.content);
```
</Tab>
</Tabs>

```text
Hi Emily! I'm here to help you. It looks like your account is currently suspended due to a payment failure. This might be the reason you're unable to log in. 

The last transaction on your account failed because the card you were using has expired. If you update your payment information, we can help you get your account reactivated. Would you like assistance with that?
```
Let's look at the memory context string Zep retrieved for the above `memory.get` call.

<Tabs group="memory-context">
<Tab title="Python" group-key="python">
```python
rich.print(memory.context)
```
</Tab>
<Tab title="Typescript" group-key="ts">
```typescript
console.log(new_memory.context);
```
</Tab>
</Tabs>

```text
FACTS and ENTITIES represent relevant context to the current conversation.

# These are the most relevant facts and their valid date ranges
# format: FACT (Date range: from - to)
<FACTS>
  - Account with ID 'Emily1c2e' has a status of 'suspended'. (2025-02-24 23:24:29 - present)
  - user has the id of Emily1c2e (2025-02-24 23:24:29 - present)
  - User with ID 'Emily1c2e' has an account with ID 'Emily1c2e'. (2025-02-24 23:24:29 - present)
  - The bug report has been escalated to the engineering team. (2024-03-16 14:27:00 - present)
  - user has the name of Emily Painter (2025-02-24 23:24:29 - present)
  - Emily is the person being assisted by SupportBot. (2025-02-24 23:24:28 - present)
  - Emily1c2e is using the character creator. (2025-02-24 23:24:28 - present)
  - The reason for the account status 'suspended' is 'payment failure'. (2025-02-24 23:24:29 - present)
  - SupportBot is part of PaintWiz support. (2025-02-24 23:24:28 - present)
  - user has the email of Emily@painters.com (2025-02-24 23:24:29 - present)
  - Emily is a user of PaintWiz. (2025-02-24 23:24:28 - present)
  - The support agent suggested that Emily manually select the boat shape from the options. (2025-02-24 23:24:29 - 
present)
  - All the people in Emily1c2e's drawings have six fingers. (2025-02-24 23:24:28 - present)
  - Emily1c2e is using the landscape generator. (2025-02-24 23:24:28 - present)
  - Emily is a user of the AI art generation. (2025-02-24 23:24:28 - present)
  - Emily states that the AI art generation is completely broken. (2025-02-24 23:24:28 - present)
  - The magic pen tool draws goats instead of boats when used by Emily. (2025-02-24 23:24:29 - present)
  - Emily1c2e tries to draw mountains. (2025-02-24 23:24:28 - present)
</FACTS>

# These are the most relevant entities
# ENTITY_NAME: entity summary
<ENTITIES>
  - goats: In a recent support interaction, a user reported a bug with the magic pen tool in a drawing application,
where attempting to draw boats resulted in the tool drawing goats instead. The user, Emily, described the issue, 
stating that whenever she selects the magic pen and draws a boat shape, it is replaced with a goat shape. The 
support agent acknowledged the problem and confirmed it would be escalated to the engineering team for resolution. 
In the meantime, the agent suggested that Emily could manually select the boat shape from the available options 
instead of using the pen tool. Emily expressed her hope for a quick fix to the issue.
  - failure_reason: Two transactions failed due to expired cards: one on September 15, 2024, and another on August 
30, 2024, for the amount of $99.99 associated with account ID 'Emily1c2e'.
  - status: User account "Emily1c2e" is suspended due to a payment failure. A transaction of $99.99 on September 
15, 2024, failed because the card ending in "1234" had expired. This card had previously been used successfully for
the same amount on July 30, 2024, but a failure on August 30, 2024, resulted in the account's suspension.
  - bug: A user reported a bug with the magic pen tool, stating that when attempting to draw boats, the tool 
instead draws goats. The support agent acknowledged the issue and requested more details about how the user was 
utilizing the tool. The user explained that they select the magic pen and draw a boat shape, but it gets replaced 
with goats. The support agent confirmed the bug and stated that it would be escalated to the engineering team for 
resolution. In the meantime, they suggested that the user manually select the boat shape from the options instead 
of using the pen. The user expressed hope for a quick fix.
  - user_id: Emily reported a bug with the magic pen tool in a drawing application, where attempting to draw boats 
resulted in goats being drawn instead. A support agent acknowledged the issue and requested more details. Emily 
explained her process, and the agent confirmed the bug, stating it would be escalated to the engineering team. As a
temporary workaround, the agent suggested manually selecting the boat shape. Emily expressed hope for a quick 
resolution. Additionally, it was noted that another user, identified as "Emily1c2e," has a suspended account due to
a payment failure.
  - people: Emily is frustrated with the AI art generation feature of PaintWiz, specifically mentioning that the 
people in her drawings are depicted with six fingers, which she finds ridiculous.
  - character creator: Emily is experiencing significant issues with the character creator feature of the app. She 
reports that when using the landscape generator and character creator, the app is malfunctioning, resulting in 
bizarre outcomes such as people in her drawings having six fingers. Emily expresses her frustration, stating that 
the AI art generation is completely broken and is not functioning as expected.
</ENTITIES>
```


---
title: Memory
subtitle: Learn how to use the Memory API to store and retrieve memory.
slug: memory
---
Zep makes memory management extremely simple: you add memory with a single line, retrieve memory with a single line, and then can immediately use the retrieved memory in your next LLM call.

The Memory API is high-level and opinionated. For a more customizable, low-level way to add and retrieve memory, see the [Graph API](/understanding-the-graph).

## Adding memory

Add your chat history to Zep using the `memory.add` method. `memory.add` is session-specific and expects data in chat message format, including a `role` name (e.g., user's real name), `role_type` (AI, human, tool), and message `content`. Zep stores the chat history and builds a user-level knowledge graph from the messages.

<Tip>
For best results, add chat history to Zep on every chat turn. That is, add both the AI and human messages in a single operation and in the order that the messages were created.
</Tip>

The example below adds messages to Zep's memory for the user in the given session:

<Tabs group="persist">
<Tab title="Python" group-key="python">
```python
from zep_cloud.client import AsyncZep
from zep_cloud.types import Message

zep_client = AsyncZep(
    api_key=API_KEY,
)

messages = [
    Message(
        role="Jane",
        role_type="user",
        content="Who was Octavia Butler?",
    )
]

await zep_client.memory.add(session_id, messages=messages)
```

</Tab>

<Tab title="TypeScript" group-key="typescript">

```typescript
import { ZepClient } from "@getzep/zep-cloud";
import type { Message } from "@getzep/zep-cloud/api";

const zepClient = new ZepClient({
  apiKey: API_KEY,
});

const messages: Message[] = [
    { role: "Jane", role_type: "user", content: "Who was Octavia Butler?" },
];

await zepClient.memory.add(sessionId, { messages });
```
</Tab>

<Tab title="Go" group-key="go">
```Go
import (
    "github.com/getzep/zep-go/v2"
    zepclient "github.com/getzep/zep-go/v2/client"
    "github.com/getzep/zep-go/v2/option"
)

zepClient := zepclient.NewClient(
    option.WithAPIKey("<YOUR_API_KEY>"),
)

response, err := zepClient.Memory.Add(
	context.TODO(),
	"sessionId",
	&zepgo.AddMemoryRequest{
		Messages: []*zepgo.Message{
			&zepgo.Message{
				Role: "Jane",
				RoleType: "user",
				Content: "Who was Octavia Butler?",
			},
		},
	},
)
```
</Tab>
</Tabs>

You can find additional arguments to `memory.add` in the [SDK reference](/sdk-reference/memory/add). Notably, for latency sensitive applications, you can set `return_context` to true which will make `memory.add` return a context string in the way that `memory.get` does (discussed below).

If you are looking to add JSON or unstructured text as memory to the graph, you will need to use our [Graph API](/adding-data-to-the-graph).

### Ignore assistant messages
You can also pass in a list of role types to ignore when adding data to the graph using the `ignore_roles` argument. For example, you may not want assistant messages to be added to the user graph; providing the assistant messages in the `memory.add` call while setting `ignore_roles` to include "assistant" will make it so that only the user messages are ingested into the graph, but the assistant messages are still used to contextualize the user messages. This is important in case the user message itself does not have enough context, such as the message "Yes." Additionally, the assistant messages will still be added to the session's message history.

## Retrieving memory
The `memory.get()` method is a user-friendly, high-level API for retrieving relevant context from Zep. It uses the latest messages of the *given session* to determine what information is most relevant from the user's knowledge graph and returns that information in a [context string](/concepts#memory-context) for your prompt. Note that although `memory.get()` only requires a session ID, it is able to return memory derived from any session of that user. The session is just used to determine what's relevant.

`memory.get` also returns recent chat messages and raw facts that may provide additional context for your agent. We recommend using these raw messages when you call your LLM provider (see below). The `memory.get` method is user and session-specific and cannot retrieve data from group graphs.

The example below gets the `memory.context` string for the given session:

<Tabs group="retrieve">
<Tab title="Python" group-key="python">
```python
memory = zep_client.memory.get(session_id="session_id")
# the context field described above
context = memory.context
```
</Tab>
<Tab title="TypeScript" group-key="typescript">
```typescript
const memory = await zep_client.memory.get("sessionId");
// the context field described above
const context = memory.context;
```
</Tab>

<Tab title="Go" group-key="go">
```Go
memory, err := zep_client.Memory.Get(context.TODO(), "sessionId", nil)
// the context field described above
context := memory.Context
```
</Tab>
</Tabs>

You can find additional arguments to `memory.get` in the [SDK reference](/sdk-reference/memory/get). Notably, you can specify a minimum [fact rating](/facts#rating-facts-for-relevancy) which will filter out any retrieved facts with a rating below the threshold, if you are using fact ratings.

If you are looking to customize how memory is retrieved, you will need to [search the graph](/searching-the-graph) and construct a [custom memory context string](/cookbook/customize-your-memory-context-string). For example, `memory.get` uses the last few messages as the search query on the graph, but using the graph API you can use whatever query you want, as well as experiment with other search parameters such as re-ranker used.


## Using memory

Once you've retrieved the [memory context string](/concepts#memory-context), or [constructed your own context string](/cookbook/customize-your-memory-context-string) by [searching the graph](/searching-the-graph), you can include this string in your system prompt:

| MessageType | Content                                                                                                    |
| ----------- | ---------------------------------------------------------------------------------------------------------- |
| `System`    | Your system prompt <br /> <br /> `{Zep context string}`                                                               |
| `Assistant` | An assistant message stored in Zep                                                                         |
| `User`      | A user message stored in Zep                                                                               |
| ...         | ...                                                                                                        |
| `User`      | The latest user message                                                                                    |


You should also include the last 4 to 6 messages of the session when calling your LLM provider. Because Zep's ingestion can take a few minutes, the context string may not include information from the last few messages; and so the context string acts as the "long-term memory," and the last few messages serve as the raw, short-term memory.

In latency sensitive applications such as voice chat bots, you can use the context string returned from `memory.add` to avoid making two API calls.

## Customizing memory

The Memory API is our high level, easy-to-use API for adding and retrieving memory. If you want to add business data or documents to memory, or further customize how memory is retrieved, you should refer to our Guides on using the graph, such as [adding data to the graph](/adding-data-to-the-graph) and [searching the graph](/searching-the-graph). We also have a cookbook on [creating a custom context string](/cookbook/customize-your-memory-context-string) using the graph API.

Additionally, [group graphs](/groups) can be used to store non-user-specific memory.

---
slug: projects
---

<Tip>API keys are specific to a project. You can create multiple keys for a single project. Visit `Project Settings` in the Zep dashboard to manage your API keys.</Tip>



Projects bundle elements like Users, Sessions, Groups, Knowledge Graphs, and settings, helping you organize data by service, environment (e.g., development or production), or other relevant criteria.


## Creating a Project
When you sign up for Zep, your first project is automatically created. You'll be asked to configure a few project-specific settings (details below). 
If you need more projects, you can create them anytime through the <a href="https://app.getzep.com/projects/create" rel="nofollow">Zep Web App</a>.

<Frame>
    <img alt="Create a new project" src="file:af532cd0-535c-4c87-b30f-81489d6ff3aa" />
</Frame>

### Project Essentials
* Unique Project Name: Choose a unique name for your project.
* Description (Optional): Optionally add a brief description of your project.

> **You can modify your project settings later from the Dashboard.**


---
slug: users
---

A User represents an individual interacting with your application. Each User can have multiple Sessions associated with them, allowing you to track and manage their interactions over time.

The unique identifier for each user is their `UserID`. This can be any string value, such as a username, email address, or UUID.

The User object and its associated Sessions provide a powerful way to manage and understand user behavior. By associating Sessions with Users, you can track the progression of conversations and interactions over time, providing valuable context and history.

In the following sections, you will learn how to manage Users and their associated Sessions.

<Note>
**Users Enable Simple User Privacy Management**

Deleting a User will delete all Sessions and session artifacts associated with that User with a single API call, making it easy to handle Right To Be Forgotten requests.
</Note>

## Ensuring your User data is correctly mapped to the Zep knowledge graph

<Tip>
Adding your user's `email`, `first_name`, and `last_name` ensures that chat messages and business data are correctly mapped to the user node in the Zep knowledge graph. 

For e.g., if business data contains your user's email address, it will be related directly to the user node.
</Tip>

You can associate rich business context with a User:

- `user_id`: A unique identifier of the user that maps to your internal User ID.
- `email`: The user's email.
- `first_name`: The user's first name.
- `last_name`: The user's last name.

## Adding a User

You can add a new user by providing the user details.
<Tabs group="users">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(api_key=API_KEY)

new_user = client.user.add(
    user_id=user_id,
    email="user@example.com",
    first_name="Jane",
    last_name="Smith",
)
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const user = await client.user.add({
  userId: user_id,
  email: "user@example.com",
  firstName: "Jane",
  lastName: "Smith",
});
```

</Tab>
</Tabs>

> Learn how to associate [Sessions with Users](/sessions)

## Getting a User

You can retrieve a user by their ID.
<Tabs group="users">

<Tab title="Python" group-key="python">

```python
user = client.user.get("user123")
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
const user = await client.user.get("user123");
```

</Tab>
</Tabs>

## Updating a User

You can update a user's details by providing the updated user details.
<Tabs group="users">

<Tab title="Python" group-key="python">

```python
updated_user = client.user.update(
    user_id=user_id,
    email="updated_user@example.com",
    first_name="Jane",
    last_name="Smith",
)
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
const updated_user = await client.user.update(user_id, {
  email: "updated_user@example.com",
  firstName: "Jane",
  lastName: "Smith",
  metadata: { foo: "updated_bar" },
});
```

</Tab>
</Tabs>

## Deleting a User

You can delete a user by their ID.
<Tabs group="users">

<Tab title="Python" group-key="python">

```python
client.user.delete("user123")
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
await client.user.delete("user123");
```

</Tab>
</Tabs>

## Getting a User's Sessions

You can retrieve all Sessions for a user by their ID.

<Tabs group="users">
<Tab title="Python" group-key="python">

```python
sessions = client.user.get_sessions("user123")
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
const sessions = await client.user.getSessions("user123");
```

</Tab>
</Tabs>

## Listing Users

You can list all users, with optional limit and cursor parameters for pagination.
<Tabs group="users">

<Tab title="Python" group-key="python">

```python
# List the first 10 users
result = client.user.list_ordered(page_size=10, page_number=1)
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
// List the first 10 users
const result = await client.user.listOrdered({
  pageSize: 10,
  pageNumber: 1,
});
```

</Tab>
</Tabs>

## Get the User Node

You can also retrieve the user's node from their graph:

<Tabs group="users">
<Tab title="Python" group-key="python">

```python
results = client.user.get_node(user_id=user_id)
user_node = results.node
print(user_node.summary)
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
const results = await client.user.getNode(userId);
const userNode = results.node;
console.log(userNode?.summary);
```

</Tab>
</Tabs>

The user node might be used to get a summary of the user or to get facts related to the user (see ["How to find facts relevant to a specific node"](/cookbook/how-to-find-facts-relevant-to-a-specific-node)).

---
slug: sessions
---

Sessions represent a conversation. Each [User](/users) can have multiple sessions, and each session is a sequence of chat messages.

Chat messages are added to sessions using [`memory.add`](/concepts#using-memoryadd), which both adds those messages to the session history and ingests those messages into the user-level knowledge graph. The user knowledge graph contains data from all of that user's sessions to create an integrated understanding of the user.

<Note>
The knowledge graph does not separate the data from different sessions, but integrates the data together to create a unified picture of the user. So the [get session memory](/sdk-reference/memory/get) endpoint and the associated [`memory.get`](/concepts#using-memoryget) method don't return memory derived only from that session, but instead return whatever user-level memory is most relevant to that session, based on the session's most recent messages.
</Note>

## Adding a Session

`SessionIDs` are arbitrary identifiers that you can map to relevant business objects in your app, such as users or a
conversation a user might have with your app. Before you create a session, make sure you have [created a user](/users#adding-a-user) first. Then create a session with:

<Tabs group="sessions">

<Tab title="Python" group-key="python">

```python
client = Zep(
    api_key=API_KEY,
)
session_id = uuid.uuid4().hex # A new session identifier

client.memory.add_session(
    session_id=session_id,
    user_id=user_id,
)
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
const client = new ZepClient({
  apiKey: API_KEY,
});

const sessionId: string = uuid.v4(); // Generate a new session identifier

await client.memory.addSession({
  sessionId: session_id,
  userId: userId,
});
```

</Tab>
</Tabs>

## Getting a Session

<Tabs group="sessions">

<Tab title="Python" group-key="python">

```python
session = client.memory.get_session(session_id)
print(session.dict())
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
const session = await client.memory.getSession(sessionId);
console.log(session);
```

</Tab>
</Tabs>

## Deleting a Session

Deleting a session deletes it and its associated messages. It does not however delete the associated data in the user's knowledge graph. To remove data from the graph, see [deleting data from the graph](/deleting-data-from-the-graph).

<Tabs group="sessions">

<Tab title="Python" group-key="python">

```python
client.memory.delete(session_id)
```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
await client.memory.delete(sessionId);
```

</Tab>
</Tabs>

## Listing Sessions

You can list all Sessions in the Zep Memory Store with page_size and page_number parameters for pagination.

<Tabs group="sessions">

<Tab title="Python" group-key="python">

```python
# List the first 10 Sessions
result = client.memory.list_sessions(page_size=10, page_number=1)
for session in result.sessions:
    print(session)

```

</Tab>
<Tab title="TypeScript" group-key="ts">

```typescript
// List the first 10 Sessions
const { sessions } = await client.memory.listSessions({
  pageSize: 10,
  pageNumber: 1,
});
console.log("First 10 Sessions:");
sessions.forEach((session) => console.log(session));
```

</Tab>
</Tabs>


---
title: Groups
subtitle: >-
  Group graphs can be used to create and manage additional non-user specific
  graphs.
slug: groups
---
A user graph is tied to a specific user; a group graph is just like a user graph, except it is not tied to a specific user. It is best thought of as an "arbitrary graph" which, for example, can be used as memory for a group of users, or for a more complex use case.

For example, a group graph could store information about a company's product, which you might not want to add to every user's graph, because that would be redundant. And when your chatbot responds, it could utilize a memory context string from both that user's graph as well as from the product group graph. See our [cookbook on this](/cookbook/how-to-share-memory-across-users-using-group-graphs) for an example.

A more complicated use case could be to create a group graph which is used when a certain topic is mentioned as opposed to when certain users require a response. For instance, anytime any user mentions "pizza" in a chat, that could trigger a call to a group graph about pizza.

<Note>
    You do not need to add/register users with a group. Instead, you just retrieve memory from the group graph when responding to any of the users you want in the group.
</Note>

## Creating a Group

<Tabs>

<Tab title="Python">

```python
group = client.group.add(
    group_id="some-group-id", 
    description="This is a description.", 
    name="Group Name"
)
```
</Tab>

<Tab title="TypeScript">

```typescript
const group = await client.group.add({
    groupId: "some-group-id",
    description: "This is a description.",
    name: "Group Name"
});
```

</Tab>

</Tabs>

## Adding Data to a Group Graph

Adding data to a group graph requires using the `graph.add` method. Below is an example, and for more on this method, see [Adding Data to the Graph](/adding-data-to-the-graph) and our [SDK Reference](/sdk-reference/graph/add).
<Tabs>

<Tab title="Python">

```python
client.graph.add(
    group_id=group_id,
    data="Hello world!",
    type="text",
)
```

</Tab>

<Tab title="TypeScript">

```typescript
await client.graph.add({
    groupId: "some-group-id",
    data: "Hello world!",
    type: "text",
});
```

</Tab>

</Tabs>

## Searching a Group Graph

Searching a group graph requires using the `graph.search` method. Below is an example, and for more on this method, see [Searching the Graph](/searching-the-graph) and our [SDK Reference](/sdk-reference/graph/search).

<Tabs>

<Tab title="Python">

```python
search_results = client.graph.search(
    group_id=group_id,
    query="Banana",
    scope="nodes",
)
```

</Tab>

<Tab title="TypeScript">

```typescript
const searchResults = await client.graph.search({
    groupId: groupId,
    query: "Banana",
    scope: "nodes",
});
```

</Tab>

</Tabs>

## Deleting a Group

<Tabs>

<Tab title="Python">

```python
client.group.delete(group_id)
```

</Tab>

<Tab title="TypeScript">

```typescript
await client.group.delete("some-group-id");
```

</Tab>

</Tabs>



---
title: Understanding the Graph
slug: understanding-the-graph
---

Zep's knowledge graph powers its facts and memory capabilities. Zep's graph is built on [Graphiti](/graphiti/graphiti/overview), Zep's open-source temporal graph library, which is fully integrated into Zep. Developers do not need to interact directly with Graphiti or understand its underlying implementation.

Zep's graph database stores data in three main types:

1. Entity edges (edges): Represent relationships between nodes and include semantic facts representing the relationship between the edge's nodes.
2. Entity nodes (nodes): Represent entities extracted from episodes, containing summaries of relevant information.
3. Episodic nodes (episodes): Represent raw data stored in Zep, either through chat history or the `graph.add` endpoint.

## Working with the Graph

To learn more about interacting with Zep's graph, refer to the following sections:

- [Adding Data to the Graph](/adding-data-to-the-graph): Learn how to add new data to the graph.
- [Reading Data from the Graph](/reading-data-from-the-graph): Discover how to retrieve information from the graph.
- [Searching the Graph](/searching-the-graph): Explore techniques for efficiently searching the graph.

These guides will help you leverage the full power of Zep's knowledge graph in your applications.

---
title: Utilizing Facts and Summaries
subtitle: >-
  Facts and summaries are extracted from the chat history as a conversation
  unfolds as well as from business data added to Zep.
slug: facts
---

## Understanding Facts and Summaries in Zep

### Facts are Precise and Time-Stamped Information
A `fact` is stored on an [edge](/sdk-reference/graph/edge/get) and captures a detailed relationship about specific events. It includes `valid_at` and `invalid_at` timestamps, ensuring temporal accuracy and preserving a clear history of changes over time. This makes facts reliable sources of truth for critical information retrieval, providing the authoritative context needed for accurate decision-making and analysis by your agent.


### Summaries are High-Level Overviews of Entities or Concepts
A `summary` resides on a [node](/sdk-reference/graph/node/get) and provides a broad snapshot of an entity or concept and its relationships to other nodes. Summaries offer an aggregated and concise representation, making it easier to understand key information at a glance.

<Tip title="Choosing Between Facts and Summaries">
Zep does not recommend relying solely on summaries for grounding LLM responses. While summaries provide a high-level overview, they lack the temporal accuracy necessary for precise reasoning. Instead, the [memory context](/concepts#memory-context) should be used since it includes relevant facts (each with valid and invalid timestamps). This ensures that conversations are based on up-to-date and contextually accurate information. 
</Tip>

## Context String
When calling [Get Session Memory](/sdk-reference/memory/get), Zep employs a sophisticated search strategy to surface the most pertinent information. The system first examines recent context by analyzing the last 4 messages (2 complete chat turns). It then utilizes multiple search techniques, with reranking steps to identify and prioritize the most contextually significant details for the current conversation.

The returned, `context` is structured as a string, optimized for language model prompts, making it easy to integrate into AI workflows. For more details, see [Key Concepts](/concepts#memory-context). In addition to the `context`, the API response includes an array of the identified `relevant_facts` with their supporting details.

## Rating Facts for Relevancy
Not all `relevant_facts` are equally important to your specific use-case. For example, a relationship coach app may need to recall important facts about a user’s family, but what the user ate for breakfast Friday last week is unimportant.

Fact ratings are a way to help Zep understand the importance of `relevant_facts` to your particular use case. After implementing fact ratings, you can specify a `minRating` when retrieving `relevant_facts` from Zep, ensuring that the memory `context` string contains customized content.

### Implementing Fact Ratings
The `fact_rating_instruction` framework consists of an instruction and three example facts, one for each of a `high`, `medium`, and `low` rating.  These are passed when [Adding a User](/sdk-reference/user/add) or [Adding a Group](/sdk-reference/group/add) and become a property of the User or Group.

### Example: Fact Rating Implementation

<Tabs>
<Tab title="Rating Facts for Poignancy" group-key="poignancy">
```python 
fact_rating_instruction = """Rate the facts by poignancy. Highly poignant 
facts have a significant emotional impact or relevance to the user. 
Facts with low poignancy are minimally relevant or of little emotional
significance."""
fact_rating_examples = FactRatingExamples(
    high="The user received news of a family member's serious illness.",
    medium="The user completed a challenging marathon.",
    low="The user bought a new brand of toothpaste.",
)
client.user.add(
    user_id=user_id,
    fact_rating_instruction=FactRatingInstruction(
        instruction=fact_rating_instruction,
        examples=fact_rating_examples,
    ),
)
```
</Tab>
<Tab title="Use Case-Specific Fact Rating" group-key="use-case">
```python 
client.user.add(
    user_id=user_id,
    fact_rating_instruction=FactRatingInstruction(
        instruction="""Rate the facts by how relevant they 
                       are to purchasing shoes.""",
        examples=FactRatingExamples(
            high="The user has agreed to purchase a Reebok running shoe.",
            medium="The user prefers running to cycling.",
            low="The user purchased a dress.",
        ),
    ),
)
```
</Tab>
</Tabs>

All facts are rated on a scale between 0 and 1.  You can access `rating` when retrieving `relevant_facts` from [Get Session Memory](/sdk-reference/memory/get).

### Limiting Memory Recall to High-Rating Facts
You can filter `relevant_facts` by setting the `minRating` parameter in [Get Session Memory](/sdk-reference/memory/get).

```python 
result = client.memory.get(session_id, min_rating=0.7)
```
## Adding or Deleting Facts or Summaries
Facts and summaries are generated as part of the ingestion process. If you follow the directions for [adding data to the graph](/adding-data-to-the-graph), new facts and summaries will be created.

Deleting facts and summaries is handled by deleting data from the graph. Facts and summaries will be deleted when you [delete the edge or node](/deleting-data-from-the-graph) they exist on.


## APIs related to Facts and Summaries
You can extract facts and summaries using the following methods:

| Method | Description |
|--------|-------------|
| [Get Session Memory](/sdk-reference/memory/get) | Retrieves the `context` string and `relevant_facts` |
| [Add User](/sdk-reference/user/add) <br/> [Update User](/sdk-reference/user/update) <br/> [Create Group](/sdk-reference/group/add) <br/> [Update Group](/sdk-reference/group/update) | Allows specifying `fact_rating_instruction` |
| [Get User](/sdk-reference/user/get)   <br/> [Get Users](/sdk-reference/user/list-ordered) <br/> [Get Group](/sdk-reference/group/get-group) <br/> [Get All Groups](/sdk-reference/group/get-all-groups) | Retrieves `fact_rating_instruction` for each user or group |
| [Search the Graph](/sdk-reference/graph/search) | Returns a list. Each item is an `edge` or `node` and has an associated `fact` or `summary` |
| [Get User Edges](/sdk-reference/graph/edge/get-by-user-id) <br/> [Get Group Edges](/sdk-reference/graph/edge/get-by-group-id) <br/> [Get Edge](/sdk-reference/graph/edge/get) | Retrieves `fact` on each `edge` |
| [Get User Nodes](/sdk-reference/graph/node/get-by-user-id) <br/> [Get Group Nodes](/sdk-reference/graph/node/get-by-group-id) <br/> [Get Node](/sdk-reference/graph/node/get) | Retrieves `summary` on each `node`|

---
title: Customizing Graph Structure
slug: customizing-graph-structure
---

Zep enables the use of rich, domain-specific data structures in graphs through Entity Types and Edge Types, replacing generic graph nodes and edges with detailed models. 

Zep classifies newly created nodes/edges as one of the default or custom types or leaves them unclassified. For example, a node representing a preference is classified as a Preference node, and attributes specific to that type are automatically populated. You may restrict graph queries to nodes/edges of a specific type, such as Preference.

The default entity types are applied to all graphs by default, but you may define additional custom types as needed.

Each node/edge is classified as a single type only. Multiple classifications are not supported.

## Default Entity Types

### Definition

The default entity types are: 
- **User**: A human that is part of the current chat thread.
- **Preference**: One of the User's preferences.
- **Procedure**: A multi-step instruction informing the agent how to behave (e.g. 'When the user asks for code, respond only with code snippets followed by a bullet point explanation')

Default entity types only apply to user graphs (not group graphs). All nodes in any user graph will be classified into one of these types or none.

### Adding Data

When we add data to the graph, default entity types are automatically created:

<CodeBlocks>
```python
from zep_cloud.types import Message

message = {"role": "John Doe", "role_type": "user", "content": "I really like pop music, and I don't like metal"}

client.memory.add(session_id=session_id, messages=[Message(**message)])
```
```typescript
import { RoleType } from "@getzep/zep-cloud/api/types";

const messages = [{ role: "John Doe", roleType: RoleType.UserRole, content: "I really like pop music, and I don't like metal" }];

await client.memory.add(sessionId, {messages: messages});
```
```go
userRole := "John Doe"
messages := []*zep.Message{
	{
		Role:     &userRole,
		Content:  "I really like pop music, and I don't like metal",
		RoleType: "user",
	},
}

// Add the messages to the graph
_, err = client.Memory.Add(
	context.TODO(),
	sessionID,
	&zep.AddMemoryRequest{
		Messages: messages,
	},
)
if err != nil {
	log.Fatal("Error adding messages:", err)
}
```
</CodeBlocks>

### Searching

When searching nodes in the graph, you may provide a list of types to filter the search by. The provided types are ORed together. Search results will only include nodes that satisfy one of the provided types:

<CodeBlocks>
```python
search_results = client.graph.search(
    user_id=user_id,
    query="the user's music preferences",
    scope="nodes",
    search_filters={
        "node_labels": ["Preference"]
    }
)
for i, node in enumerate(search_results.nodes):
    preference = node.attributes
    print(f"Preference {i+1}:{preference}")
```
```typescript
const searchResults = await client.graph.search({
  userId: userId,
  query: "the user's music preferences",
  scope: "nodes",
  searchFilters: {
    nodeLabels: ["Preference"],
  },
});

if (searchResults.nodes && searchResults.nodes.length > 0) {
  for (let i = 0; i < searchResults.nodes.length; i++) {
    const node = searchResults.nodes[i];
    const preference = node.attributes;
    console.log(`Preference ${i + 1}: ${JSON.stringify(preference)}`);
  }
}
```
```go
searchFilters := zep.SearchFilters{NodeLabels: []string{"Preference"}}
searchResults, err := client.Graph.Search(
	ctx,
	&zep.GraphSearchQuery{
		UserID:        zep.String(userID),
		Query:         "the user's music preferences",
		Scope:         zep.GraphSearchScopeNodes.Ptr(),
		SearchFilters: &searchFilters,
	},
)
if err != nil {
	log.Fatal("Error searching graph:", err)
}

for i, node := range searchResults.Nodes {
	// Convert attributes map to JSON for pretty printing
	attributesJSON, err := json.MarshalIndent(node.Attributes, "", "  ")
	if err != nil {
		log.Fatal("Error marshaling attributes:", err)
	}
	
	fmt.Printf("Preference %d:\n%s\n\n", i+1, string(attributesJSON))
}
```
</CodeBlocks>

```text
Preference 1: {'category': 'Music', 'description': 'Pop Music is a genre of music characterized by its catchy melodies and widespread appeal.', 'labels': ['Entity', 'Preference']}
Preference 2: {'category': 'Music', 'description': 'Metal Music is a genre of music characterized by its heavy sound and complex compositions.', 'labels': ['Entity', 'Preference']}
```

## Custom Entity and Edge Types

### Definition

In addition to the default entity types, you may specify your own custom entity and custom edge types. You need to provide a description of the type and a description for each of the fields. The syntax for this is different for each language.

You may not create more than 10 custom entity types and 10 custom edge types per project. The limit of 10 custom entity types does not include the default types. Each model may have up to 10 fields.

<Warning>
When creating custom entity or edge types, you may not use the following attribute names (including in Go struct tags), as they conflict with default node attributes: `uuid`, `name`, `group_id`, `name_embedding`, `summary`, and `created_at`.
</Warning>

<CodeBlocks>
```python
from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel, EntityBoolean
from pydantic import Field

class Restaurant(EntityModel):
    """
    Represents a specific restaurant.
    """
    cuisine_type: EntityText = Field(description="The cuisine type of the restaurant, for example: American, Mexican, Indian, etc.", default=None)
    dietary_accommodation: EntityText = Field(description="The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc.", default=None)

class Audiobook(EntityModel):
    """
    Represents an audiobook entity.
    """
    genre: EntityText = Field(description="The genre of the audiobook, for example: self-help, fiction, nonfiction, etc.", default=None)

class RestaurantVisit(EdgeModel):
    """
    Represents the fact that the user visited a restaurant.
    """
    restaurant_name: EntityText = Field(description="The name of the restaurant the user visited", default=None)

class AudiobookListen(EdgeModel):
    """
    Represents the fact that the user listened to or played an audiobook.
    """
    audiobook_title: EntityText = Field(description="The title of the audiobook the user listened to or played", default=None)

class DietaryPreference(EdgeModel):
    """
    Represents the fact that the user has a dietary preference or dietary restriction.
    """
    preference_type: EntityText = Field(description="Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc.", default=None)
    allergy: EntityBoolean = Field(description="Whether this dietary preference represents a user allergy: True or false", default=None)
```
```typescript
import { entityFields, EntityType, EdgeType } from "@getzep/zep-cloud/wrapper/ontology";

const RestaurantSchema: EntityType = {
    description: "Represents a specific restaurant.",
    fields: {
        cuisine_type: entityFields.text("The cuisine type of the restaurant, for example: American, Mexican, Indian, etc."),
        dietary_accommodation: entityFields.text("The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc."),
    },
};

const AudiobookSchema: EntityType = {
    description: "Represents an audiobook entity.",
    fields: {
        genre: entityFields.text("The genre of the audiobook, for example: self-help, fiction, nonfiction, etc."),
    },
};

const RestaurantVisit: EdgeType = {
    description: "Represents the fact that the user visited a restaurant.",
    fields: {
        restaurant_name: entityFields.text("The name of the restaurant the user visited"),
    },
    sourceTargets: [
        { source: "User", target: "Restaurant" },
    ],
};

const AudiobookListen: EdgeType = {
    description: "Represents the fact that the user listened to or played an audiobook.",
    fields: {
        audiobook_title: entityFields.text("The title of the audiobook the user listened to or played"),
    },
    sourceTargets: [
        { source: "User", target: "Audiobook" },
    ],
};

const DietaryPreference: EdgeType = {
    description: "Represents the fact that the user has a dietary preference or dietary restriction.",
    fields: {
        preference_type: entityFields.text("Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc."),
        allergy: entityFields.boolean("Whether this dietary preference represents a user allergy: True or false"),
    },
    sourceTargets: [
        { source: "User" },
    ],
};
```
```go
type Restaurant struct {
    zep.BaseEntity `name:"Restaurant" description:"Represents a specific restaurant."`
    CuisineType           string `description:"The cuisine type of the restaurant, for example: American, Mexican, Indian, etc." json:"cuisine_type,omitempty"`
    DietaryAccommodation  string `description:"The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc." json:"dietary_accommodation,omitempty"`
}

type Audiobook struct {
    zep.BaseEntity `name:"Audiobook" description:"Represents an audiobook entity."`
    Genre string `description:"The genre of the audiobook, for example: self-help, fiction, nonfiction, etc." json:"genre,omitempty"`
}

type RestaurantVisit struct {
    zep.BaseEdge `name:"RESTAURANT_VISIT" description:"Represents the fact that the user visited a restaurant."`
    RestaurantName string `description:"The name of the restaurant the user visited" json:"restaurant_name,omitempty"`
}

type AudiobookListen struct {
    zep.BaseEdge `name:"AUDIOBOOK_LISTEN" description:"Represents the fact that the user listened to or played an audiobook."`
    AudiobookTitle string `description:"The title of the audiobook the user listened to or played" json:"audiobook_title,omitempty"`
}

type DietaryPreference struct {
    zep.BaseEdge `name:"DIETARY_PREFERENCE" description:"Represents the fact that the user has a dietary preference or dietary restriction."`
    PreferenceType string `description:"Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc." json:"preference_type,omitempty"`
    Allergy        bool   `description:"Whether this dietary preference represents a user allergy: True or false" json:"allergy,omitempty"`
}
```
</CodeBlocks>

### Setting Entity and Edge Types

You can then set these custom entity and edge types as the graph ontology for your current [Zep project](/projects). Note that for custom edge types, you can require the source and destination nodes to be a certain type, or allow them to be any type:

<CodeBlocks>
```python
from zep_cloud import EntityEdgeSourceTarget

client.graph.set_ontology(
    entities={
        "Restaurant": Restaurant,
        "Audiobook": Audiobook,
    },
    edges={
        "RESTAURANT_VISIT": (
            RestaurantVisit,
            [EntityEdgeSourceTarget(source="User", target="Restaurant")]
        ),
        "AUDIOBOOK_LISTEN": (
            AudiobookListen,
            [EntityEdgeSourceTarget(source="User", target="Audiobook")]
        ),
        "DIETARY_PREFERENCE": (
            DietaryPreference,
            [EntityEdgeSourceTarget(source="User")]
        ),
    }
)
```
```typescript
await client.graph.setOntology(
    {
        Restaurant: RestaurantSchema,
        Audiobook: AudiobookSchema,
    },
    {
        RESTAURANT_VISIT: RestaurantVisit,
        AUDIOBOOK_LISTEN: AudiobookListen,
        DIETARY_PREFERENCE: DietaryPreference,
    }
);
```
```go
_, err = client.Graph.SetOntology(
    ctx,
    []zep.EntityDefinition{
        Restaurant{},
        Audiobook{},
    },
    []zep.EdgeDefinitionWithSourceTargets{
        {
            EdgeModel: RestaurantVisit{},
            SourceTargets: []zep.EntityEdgeSourceTarget{
                {
                    Source: zep.String("User"),
                    Target: zep.String("Restaurant"),
                },
            },
        },
        {
            EdgeModel: AudiobookListen{},
            SourceTargets: []zep.EntityEdgeSourceTarget{
                {
                    Source: zep.String("User"),
                    Target: zep.String("Audiobook"),
                },
            },
        },
        {
            EdgeModel: DietaryPreference{},
            SourceTargets: []zep.EntityEdgeSourceTarget{
                {
                    Source: zep.String("User"),
                },
            },
        },
    },
)
if err != nil {
    fmt.Printf("Error setting ontology: %v\n", err)
    return
}
```
</CodeBlocks>

### Adding Data

Now, when you add data to the graph, new nodes and edges are classified into exactly one of the overall set of entity or edge types respectively, or no type:

<CodeBlocks>
```python
from zep_cloud import Message
import uuid

messages_session1 = [
    Message(content="Take me to a lunch place", role_type="user", role="John Doe"),
    Message(content="How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", role_type="assistant", role="Assistant"),
    Message(content="Do any of those have vegetarian options? I’m vegetarian", role_type="user", role="John Doe"),
    Message(content="Yes, Green Leaf Cafe has vegetarian options", role_type="assistant", role="Assistant"),
    Message(content="Let’s go to Green Leaf Cafe", role_type="user", role="John Doe"),
    Message(content="Navigating to Green Leaf Cafe", role_type="assistant", role="Assistant"),
]

messages_session2 = [
    Message(content="Play the 7 habits of highly effective people", role_type="user", role="John Doe"),
    Message(content="Playing the 7 habits of highly effective people", role_type="assistant", role="Assistant"),
]

user_id = f"user-{uuid.uuid4()}"
client.user.add(user_id=user_id, first_name="John", last_name="Doe", email="john.doe@example.com")

session1_id = f"session-{uuid.uuid4()}"
session2_id = f"session-{uuid.uuid4()}"
client.memory.add_session(session_id=session1_id, user_id=user_id)
client.memory.add_session(session_id=session2_id, user_id=user_id)

client.memory.add(session_id=session1_id, messages=messages_session1, ignore_roles=["assistant"])
client.memory.add(session_id=session2_id, messages=messages_session2, ignore_roles=["assistant"])
```
```typescript
import { v4 as uuidv4 } from "uuid";
import type { Message } from "@getzep/zep-cloud/api";

const messagesSession1: Message[] = [
    { content: "Take me to a lunch place", roleType: "user", role: "John Doe" },
    { content: "How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", roleType: "assistant", role: "Assistant" },
    { content: "Do any of those have vegetarian options? I’m vegetarian", roleType: "user", role: "John Doe" },
    { content: "Yes, Green Leaf Cafe has vegetarian options", roleType: "assistant", role: "Assistant" },
    { content: "Let’s go to Green Leaf Cafe", roleType: "user", role: "John Doe" },
    { content: "Navigating to Green Leaf Cafe", roleType: "assistant", role: "Assistant" },
];

const messagesSession2: Message[] = [
    { content: "Play the 7 habits of highly effective people", roleType: "user", role: "John Doe" },
    { content: "Playing the 7 habits of highly effective people", roleType: "assistant", role: "Assistant" },
];

let userId = `user-${uuidv4()}`;
await client.user.add({ userId, firstName: "John", lastName: "Doe", email: "john.doe@example.com" });

const session1Id = `session-${uuidv4()}`;
const session2Id = `session-${uuidv4()}`;
await client.memory.addSession({ sessionId: session1Id, userId });
await client.memory.addSession({ sessionId: session2Id, userId });

await client.memory.add(session1Id, { messages: messagesSession1, ignoreRoles: ["assistant"] });
await client.memory.add(session2Id, { messages: messagesSession2, ignoreRoles: ["assistant"] });
```
```go
messagesSession1 := []zep.Message{
    {Content: "Take me to a lunch place", RoleType: "user", Role: zep.String("John Doe")},
    {Content: "How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", RoleType: "assistant", Role: zep.String("Assistant")},
    {Content: "Do any of those have vegetarian options? I'm vegetarian", RoleType: "user", Role: zep.String("John Doe")},
    {Content: "Yes, Green Leaf Cafe has vegetarian options", RoleType: "assistant", Role: zep.String("Assistant")},
    {Content: "Let's go to Green Leaf Cafe", RoleType: "user", Role: zep.String("John Doe")},
    {Content: "Navigating to Green Leaf Cafe", RoleType: "assistant", Role: zep.String("Assistant")},
}
messagesSession2 := []zep.Message{
    {Content: "Play the 7 habits of highly effective people", RoleType: "user", Role: zep.String("John Doe")},
    {Content: "Playing the 7 habits of highly effective people", RoleType: "assistant", Role: zep.String("Assistant")},
}
userID := "user-" + uuid.NewString()
userReq := &zep.CreateUserRequest{
    UserID:    userID,
    FirstName: zep.String("John"),
    LastName:  zep.String("Doe"),
    Email:     zep.String("john.doe@example.com"),
}
_, err = client.User.Add(ctx, userReq)
if err != nil {
    fmt.Printf("Error creating user: %v\n", err)
    return
}

session1ID := "session-" + uuid.NewString()
session2ID := "session-" + uuid.NewString()

session1Req := &zep.CreateSessionRequest{
    SessionID: session1ID,
    UserID:    userID,
}
session2Req := &zep.CreateSessionRequest{
    SessionID: session2ID,
    UserID:    userID,
}
_, err = client.Memory.AddSession(ctx, session1Req)
if err != nil {
    fmt.Printf("Error creating session 1: %v\n", err)
    return
}
_, err = client.Memory.AddSession(ctx, session2Req)
if err != nil {
    fmt.Printf("Error creating session 2: %v\n", err)
    return
}

msgPtrs1 := make([]*zep.Message, len(messagesSession1))
for i := range messagesSession1 {
    msgPtrs1[i] = &messagesSession1[i]
}
addReq1 := &zep.AddMemoryRequest{
    Messages: msgPtrs1,
    IgnoreRoles: []zep.RoleType{
        zep.RoleTypeAssistantRole,
    },
}
_, err = client.Memory.Add(ctx, session1ID, addReq1)
if err != nil {
    fmt.Printf("Error adding messages to session 1: %v\n", err)
    return
}

msgPtrs2 := make([]*zep.Message, len(messagesSession2))
for i := range messagesSession2 {
    msgPtrs2[i] = &messagesSession2[i]
}
addReq2 := &zep.AddMemoryRequest{
    Messages: msgPtrs2,
    IgnoreRoles: []zep.RoleType{
        zep.RoleTypeAssistantRole,
    },
}
_, err = client.Memory.Add(ctx, session2ID, addReq2)
if err != nil {
    fmt.Printf("Error adding messages to session 2: %v\n", err)
    return
}
```
</CodeBlocks>

### Searching/Retrieving

Now that a graph with custom entity and edge types has been created, you may filter node search results by entity type, or edge search results by edge type.

Below, you can see the examples that were created from our data of each of the entity and edge types that we defined:
<CodeBlocks>
```python
search_results_restaurants = client.graph.search(
    user_id=user_id,
    query="Take me to a restaurant",
    scope="nodes",
    search_filters={
        "node_labels": ["Restaurant"]
    },
    limit=1,
)
node = search_results_restaurants.nodes[0]
print(f"Node name: {node.name}")
print(f"Node labels: {node.labels}")
print(f"Cuisine type: {node.attributes.get('cuisine_type')}")
print(f"Dietary accommodation: {node.attributes.get('dietary_accommodation')}")
```
```typescript
let searchResults = await client.graph.search({
    userId: userId,
    query: "Take me to a restaurant",
    scope: "nodes",
    searchFilters: { nodeLabels: ["Restaurant"] },
    limit: 1,
});
if (searchResults.nodes && searchResults.nodes.length > 0) {
    const node = searchResults.nodes[0];
    console.log(`Node name: ${node.name}`);
    console.log(`Node labels: ${node.labels}`);
    console.log(`Cuisine type: ${node.attributes?.cuisine_type}`);
    console.log(`Dietary accommodation: ${node.attributes?.dietary_accommodation}`);
}
```
```go
searchFiltersRestaurants := zep.SearchFilters{NodeLabels: []string{"Restaurant"}}
searchResultsRestaurants, err := client.Graph.Search(
    ctx,
    &zep.GraphSearchQuery{
        UserID:        zep.String(userID),
        Query:         "Take me to a restaurant",
        Scope:         zep.GraphSearchScopeNodes.Ptr(),
        SearchFilters: &searchFiltersRestaurants,
        Limit:         zep.Int(1),
    },
)
if err != nil {
    fmt.Printf("Error searching graph (Restaurant node): %v\n", err)
    return
}
if len(searchResultsRestaurants.Nodes) > 0 {
    node := searchResultsRestaurants.Nodes[0]
    fmt.Printf("Node name: %s\n", node.Name)
    fmt.Printf("Node labels: %v\n", node.Labels)
    fmt.Printf("Cuisine type: %v\n", node.Attributes["cuisine_type"])
    fmt.Printf("Dietary accommodation: %v\n", node.Attributes["dietary_accommodation"])
}
```
</CodeBlocks>

```text
Node name: Green Leaf Cafe
Node labels: Entity,Restaurant
Cuisine type: undefined
Dietary accommodation: vegetarian
```
<CodeBlocks>
```python
search_results_audiobook_nodes = client.graph.search(
    user_id=user_id,
    query="Play an audiobook",
    scope="nodes",
    search_filters={
        "node_labels": ["Audiobook"]
    },
    limit=1,
)
node = search_results_audiobook_nodes.nodes[0]
print(f"Node name: {node.name}")
print(f"Node labels: {node.labels}")
print(f"Genre: {node.attributes.get('genre')}")
```
```typescript
searchResults = await client.graph.search({
    userId: userId,
    query: "Play an audiobook",
    scope: "nodes",
    searchFilters: { nodeLabels: ["Audiobook"] },
    limit: 1,
});
if (searchResults.nodes && searchResults.nodes.length > 0) {
    const node = searchResults.nodes[0];
    console.log(`Node name: ${node.name}`);
    console.log(`Node labels: ${node.labels}`);
    console.log(`Genre: ${node.attributes?.genre}`);
}
```
```go
searchFiltersAudiobook := zep.SearchFilters{NodeLabels: []string{"Audiobook"}}
searchResultsAudiobook, err := client.Graph.Search(
    ctx,
    &zep.GraphSearchQuery{
        UserID:        zep.String(userID),
        Query:         "Play an audiobook",
        Scope:         zep.GraphSearchScopeNodes.Ptr(),
        SearchFilters: &searchFiltersAudiobook,
        Limit:         zep.Int(1),
    },
)
if err != nil {
    fmt.Printf("Error searching graph (Audiobook node): %v\n", err)
    return
}
if len(searchResultsAudiobook.Nodes) > 0 {
    node := searchResultsAudiobook.Nodes[0]
    fmt.Printf("Node name: %s\n", node.Name)
    fmt.Printf("Node labels: %v\n", node.Labels)
    fmt.Printf("Genre: %v\n", node.Attributes["genre"])
}
```
</CodeBlocks>

```text
Node name: 7 habits of highly effective people
Node labels: Entity,Audiobook
Genre: undefined
```
<CodeBlocks>
```python
search_results_visits = client.graph.search(
    user_id=user_id,
    query="Take me to a restaurant",
    scope="edges",
    search_filters={
        "edge_types": ["RESTAURANT_VISIT"]
    },
    limit=1,
)
edge = search_results_visits.edges[0]
print(f"Edge fact: {edge.fact}")
print(f"Edge type: {edge.name}")
print(f"Restaurant name: {edge.attributes.get('restaurant_name')}")
```
```typescript
searchResults = await client.graph.search({
    userId: userId,
    query: "Take me to a restaurant",
    scope: "edges",
    searchFilters: { edgeTypes: ["RESTAURANT_VISIT"] },
    limit: 1,
});
if (searchResults.edges && searchResults.edges.length > 0) {
    const edge = searchResults.edges[0];
    console.log(`Edge fact: ${edge.fact}`);
    console.log(`Edge type: ${edge.name}`);
    console.log(`Restaurant name: ${edge.attributes?.restaurant_name}`);
}
```
```go
searchFiltersVisits := zep.SearchFilters{EdgeTypes: []string{"RESTAURANT_VISIT"}}
searchResultsVisits, err := client.Graph.Search(
    ctx,
    &zep.GraphSearchQuery{
        UserID:        zep.String(userID),
        Query:         "Take me to a restaurant",
        Scope:         zep.GraphSearchScopeEdges.Ptr(),
        SearchFilters: &searchFiltersVisits,
        Limit:         zep.Int(1),
    },
)
if err != nil {
    fmt.Printf("Error searching graph (RESTAURANT_VISIT): %v\n", err)
    return
}
if len(searchResultsVisits.Edges) > 0 {
    edge := searchResultsVisits.Edges[0]
    var visit RestaurantVisit
    err := zep.UnmarshalEdgeAttributes(edge.Attributes, &visit)
    if err != nil {
        fmt.Printf("\t\tError converting edge to RestaurantVisit struct: %v\n", err)
    } else {
        fmt.Printf("Edge fact: %s\n", edge.Fact)
        fmt.Printf("Edge type: %s\n", edge.Name)
        fmt.Printf("Restaurant name: %s\n", visit.RestaurantName)
    }
}
```
</CodeBlocks>

```text
Edge fact: User John Doe is going to Green Leaf Cafe
Edge type: RESTAURANT_VISIT
Restaurant name: Green Leaf Cafe
```
<CodeBlocks>
```python
search_results_audiobook_listens = client.graph.search(
    user_id=user_id,
    query="Play an audiobook",
    scope="edges",
    search_filters={
        "edge_types": ["AUDIOBOOK_LISTEN"]
    },
    limit=1,
)
edge = search_results_audiobook_listens.edges[0]
print(f"Edge fact: {edge.fact}")
print(f"Edge type: {edge.name}")
print(f"Audiobook title: {edge.attributes.get('audiobook_title')}")
```
```typescript
searchResults = await client.graph.search({
    userId: userId,
    query: "Play an audiobook",
    scope: "edges",
    searchFilters: { edgeTypes: ["AUDIOBOOK_LISTEN"] },
    limit: 1,
});
if (searchResults.edges && searchResults.edges.length > 0) {
    const edge = searchResults.edges[0];
    console.log(`Edge fact: ${edge.fact}`);
    console.log(`Edge type: ${edge.name}`);
    console.log(`Audiobook title: ${edge.attributes?.audiobook_title}`);
}
```
```go
searchFiltersAudiobookListen := zep.SearchFilters{EdgeTypes: []string{"AUDIOBOOK_LISTEN"}}
searchResultsAudiobookListen, err := client.Graph.Search(
    ctx,
    &zep.GraphSearchQuery{
        UserID:        zep.String(userID),
        Query:         "Play an audiobook",
        Scope:         zep.GraphSearchScopeEdges.Ptr(),
        SearchFilters: &searchFiltersAudiobookListen,
        Limit:         zep.Int(1),
    },
)
if err != nil {
    fmt.Printf("Error searching graph (AUDIOBOOK_LISTEN): %v\n", err)
    return
}
if len(searchResultsAudiobookListen.Edges) > 0 {
    edge := searchResultsAudiobookListen.Edges[0]
    var listen AudiobookListen
    err := zep.UnmarshalEdgeAttributes(edge.Attributes, &listen)
    if err != nil {
        fmt.Printf("Error converting edge to AudiobookListen struct: %v\n", err)
    } else {
        fmt.Printf("Edge fact: %s\n", edge.Fact)
        fmt.Printf("Edge type: %s\n", edge.Name)
        fmt.Printf("Audiobook title: %s\n", listen.AudiobookTitle)
    }
}
```
</CodeBlocks>

```text
Edge fact: John Doe requested to play the audiobook '7 habits of highly effective people'
Edge type: AUDIOBOOK_LISTEN
Audiobook title: 7 habits of highly effective people
```
<CodeBlocks>
```python
search_results_dietary_preference = client.graph.search(
    user_id=user_id,
    query="Find some food around here",
    scope="edges",
    search_filters={
        "edge_types": ["DIETARY_PREFERENCE"]
    },
    limit=1,
)
edge = search_results_dietary_preference.edges[0]
print(f"Edge fact: {edge.fact}")
print(f"Edge type: {edge.name}")
print(f"Preference type: {edge.attributes.get('preference_type')}")
print(f"Allergy: {edge.attributes.get('allergy')}")
```
```typescript
searchResults = await client.graph.search({
    userId: userId,
    query: "Find some food around here",
    scope: "edges",
    searchFilters: { edgeTypes: ["DIETARY_PREFERENCE"] },
    limit: 1,
});
if (searchResults.edges && searchResults.edges.length > 0) {
    const edge = searchResults.edges[0];
    console.log(`Edge fact: ${edge.fact}`);
    console.log(`Edge type: ${edge.name}`);
    console.log(`Preference type: ${edge.attributes?.preference_type}`);
    console.log(`Allergy: ${edge.attributes?.allergy}`);
}
```
```go
searchFiltersDietary := zep.SearchFilters{EdgeTypes: []string{"DIETARY_PREFERENCE"}}
searchResultsDietary, err := client.Graph.Search(
    ctx,
    &zep.GraphSearchQuery{
        UserID:        zep.String(userID),
        Query:         "Find some food around here",
        Scope:         zep.GraphSearchScopeEdges.Ptr(),
        SearchFilters: &searchFiltersDietary,
        Limit:         zep.Int(1),
    },
)
if err != nil {
    fmt.Printf("Error searching graph (DIETARY_PREFERENCE): %v\n", err)
    return
}
if len(searchResultsDietary.Edges) > 0 {
    edge := searchResultsDietary.Edges[0]
    var dietary DietaryPreference
    err := zep.UnmarshalEdgeAttributes(edge.Attributes, &dietary)
    if err != nil {
        fmt.Printf("Error converting edge to DietaryPreference struct: %v\n", err)
    } else {
        fmt.Printf("Edge fact: %s\n", edge.Fact)
        fmt.Printf("Edge type: %s\n", edge.Name)
        fmt.Printf("Preference type: %s\n", dietary.PreferenceType)
        fmt.Printf("Allergy: %v\n", dietary.Allergy)
    }
}
```
</CodeBlocks>

```text
Edge fact: User states 'I'm vegetarian' indicating a dietary preference.
Edge type: DIETARY_PREFERENCE
Preference type: vegetarian
Allergy: false
```

Additionally, you can provide multiple types in search filters, and the types will be ORed together:

<CodeBlocks>
```python
search_results_dietary_preference = client.graph.search(
    user_id=user_id,
    query="Find some food around here",
    scope="edges",
    search_filters={
        "edge_types": ["DIETARY_PREFERENCE", "RESTAURANT_VISIT"]
    },
    limit=2,
)
for edge in search_results_dietary_preference.edges:
    print(f"Edge fact: {edge.fact}")
    print(f"Edge type: {edge.name}")
    if edge.name == "DIETARY_PREFERENCE":
        print(f"Preference type: {edge.attributes.get('preference_type')}")
        print(f"Allergy: {edge.attributes.get('allergy')}")
    elif edge.name == "RESTAURANT_VISIT":
        print(f"Restaurant name: {edge.attributes.get('restaurant_name')}")
    print("\n")
```
```typescript
searchResults = await client.graph.search({
    userId: userId,
    query: "Find some food around here",
    scope: "edges",
    searchFilters: { edgeTypes: ["DIETARY_PREFERENCE", "RESTAURANT_VISIT"] },
    limit: 2,
});
if (searchResults.edges && searchResults.edges.length > 0) {
    for (const edge of searchResults.edges) {
        console.log(`Edge fact: ${edge.fact}`);
        console.log(`Edge type: ${edge.name}`);
        if (edge.name === "DIETARY_PREFERENCE") {
            console.log(`Preference type: ${edge.attributes?.preference_type}`);
            console.log(`Allergy: ${edge.attributes?.allergy}`);
        } else if (edge.name === "RESTAURANT_VISIT") {
            console.log(`Restaurant name: ${edge.attributes?.restaurant_name}`);
        }
        console.log("\n");
    }
}
```
```go
searchFiltersDietaryAndRestaurantVisit := zep.SearchFilters{EdgeTypes: []string{"DIETARY_PREFERENCE", "RESTAURANT_VISIT"}}
searchResultsDietaryAndRestaurantVisit, err := client.Graph.Search(
    ctx,
    &zep.GraphSearchQuery{
        UserID:        zep.String(userID),
        Query:         "Find some food around here",
        Scope:         zep.GraphSearchScopeEdges.Ptr(),
        SearchFilters: &searchFiltersDietaryAndRestaurantVisit,
        Limit:         zep.Int(2),
    },
)
if err != nil {
    fmt.Printf("Error searching graph (DIETARY_PREFERENCE and RESTAURANT_VISIT): %v\n", err)
    return
}
if len(searchResultsDietaryAndRestaurantVisit.Edges) > 0 {
    for _, edge := range searchResultsDietaryAndRestaurantVisit.Edges {
        switch edge.Name {
        case "DIETARY_PREFERENCE":
            var dietary DietaryPreference
            err := zep.UnmarshalEdgeAttributes(edge.Attributes, &dietary)
            if err != nil {
                fmt.Printf("Error converting edge to DietaryPreference struct: %v\n", err)
            } else {
                fmt.Printf("Edge fact: %s\n", edge.Fact)
                fmt.Printf("Edge type: %s\n", edge.Name)
                fmt.Printf("Preference type: %s\n", dietary.PreferenceType)
                fmt.Printf("Allergy: %v\n", dietary.Allergy)
            }
        case "RESTAURANT_VISIT":
            var visit RestaurantVisit
            err := zep.UnmarshalEdgeAttributes(edge.Attributes, &visit)
            if err != nil {
                fmt.Printf("Error converting edge to RestaurantVisit struct: %v\n", err)
            } else {
                fmt.Printf("Edge fact: %s\n", edge.Fact)
                fmt.Printf("Edge type: %s\n", edge.Name)
                fmt.Printf("Restaurant name: %s\n", visit.RestaurantName)
            }
        default:
            fmt.Printf("Unknown edge type: %s\n", edge.Name)
        }
        fmt.Println()
    }
}
```
</CodeBlocks>

```text
Edge fact: User John Doe is going to Green Leaf Cafe
Edge type: RESTAURANT_VISIT
Restaurant name: Green Leaf Cafe
```
```text
Edge fact: User states 'I'm vegetarian' indicating a dietary preference.
Edge type: DIETARY_PREFERENCE
Preference type: vegetarian
Allergy: false
```

### Important Notes/Tips

Some notes regarding custom entity and edge types:
- The `set_ontology` method overwrites any previously defined custom entity and edge types, so the set of custom entity and edge types is always the list of types provided in the last `set_ontology` method call
- The overall set of entity types for a project includes both the custom entity types you set and the default entity types
- There are no default edge types
- You can overwrite the default entity types by providing custom entity types with the same names
- Changing the custom entity or edge types will not update previously created nodes or edges. The classification and attributes of existing nodes and edges will stay the same. The only thing that can change existing classifications or attributes is adding data that provides new information.
- When creating custom entity or edge types, avoid using the following attribute names (including in Go struct tags), as they conflict with default attributes: `uuid`, `name`, `group_id`, `name_embedding`, `summary`, and `created_at`
- **Tip**: Design custom entity types to represent entities/nouns, and design custom edge types to represent relationships/verbs. Otherwise, your type might be represented in the graph as an edge more often than as a node or vice versa.
- **Tip**: If you have overlapping entity or edge types (e.g. 'Hobby' and 'Hiking'), you can prioritize one type over another by mentioning which to prioritize in the entity or edge type descriptions

---
title: Adding Data to the Graph
slug: adding-data-to-the-graph
---

## Overview
<Warning>
    Requests to add data to the same graph are completed sequentially to ensure the graph is built correctly. A large number of calls to add data to the same graph may result in lengthy processing times.
</Warning>

In addition to incorporating memory through chat history, Zep offers the capability to add data directly to the graph.
Zep supports three distinct data types: message, text, and JSON.

The message type is ideal for adding data in the form of chat messages that are not directly associated with a Zep [Session's](/sessions) chat history. This encompasses any communication with a designated speaker, such as emails or previous chat logs.

The text type is designed for raw text data without a specific speaker attribution. This category includes content from internal documents, wiki articles, or company handbooks. It's important to note that Zep does not process text directly from links or files.

The JSON type may be used to add any JSON document to Zep. This may include REST API responses or JSON-formatted business data.

<Note>
The `graph.add` endpoint has a data size limit of 10,000 characters.
</Note>

You can add data to either a user graph by providing a `user_id`, or to a [group graph](/groups) by specifying a `group_id`.

## Adding Message Data

Here's an example demonstrating how to add message data to the graph:

<Tabs group="graph-add">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

message = "Paul (user): I went to Eric Clapton concert last night"

new_episode = client.graph.add(
    user_id="user123",    # Optional user ID
    type="message",       # Specify type as "message"
    data=message
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const message = "User: I really enjoy working with TypeScript and React";

const newEpisode = await client.graph.add({
    userId: "user123",
    type: "message",
    data: message
});
```

</Tab>
</Tabs>

## Adding Text Data

Here's an example demonstrating how to add text data to the graph:

<Tabs group="graph-add">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

new_episode = client.graph.add(
    user_id="user123",  # Optional user ID
    type="text",        # Specify type as "text" 
    data="The user is an avid fan of Eric Clapton"
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const newEpisode = await client.graph.add({
    userId: "user123",  // Required: either userId or groupId
    type: "text",
    data: "The user is interested in machine learning and artificial intelligence"
});

```

</Tab>
</Tabs>

## Adding JSON Data

Here's an example demonstrating how to add JSON data to the graph:

<Tabs group="graph-add">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep
import json

client = Zep(
    api_key=API_KEY,
)

json_data = {"name": "Eric Clapton", "age": 78, "genre": "Rock"}
json_string = json.dumps(json_data)
new_episode = client.graph.add(
    user_id=user_id,
    type="json",
    data=json_string,
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const jsonString = '{"name": "Eric Clapton", "age": 78, "genre": "Rock"}';
const newEpisode = await client.graph.add({
    userId: userId,
    type: "json",
    data: jsonString,
});
```

</Tab>
</Tabs>

## Adding Custom Fact/Node Triplets

You can also add manually specified fact/node triplets to the graph. You need only specify the fact, the target node name, and the source node name. Zep will then create a new corresponding edge and nodes, or use an existing edge/nodes if they exist and seem to represent the same nodes or edge you send as input. And if this new fact invalidates an existing fact, it will mark the existing fact as invalid and add the new fact triplet.

<Tabs group="graph-add-triplet">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

client.graph.add_fact_triple(
    user_id=user_id,
    fact="Paul met Eric",
    fact_name="MET",
    target_node_name="Eric Clapton",
    source_node_name="Paul",
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

await client.graph.addFactTriple({
  userId: userId,
  fact: "Paul met Eric",
  factName: "MET",
  targetNodeName: "Eric Clapton",
  sourceNodeName: "Paul",
});
```

</Tab>
</Tabs>

You can also specify the node summaries, edge temporal data, and UUIDs. See the [associated SDK reference](/sdk-reference/graph/add-fact-triple).

## Add Batch Data

The batch add method is designed for efficiently adding a large amount of data to a user or group graph concurrently. This method is suitable when the data does not have a significant temporal dimension, such as static documents or bulk imports.

Normally, data added to the graph is processed sequentially. This allows the knowledge graph to capture temporal relationships and understand when one event occurs after another. When using the batch add method, each episode is processed concurrently. As a result, temporal relationships between episodes are not captured.

The batch add method is best used for static data where the order of events is not important. It is not recommended for evolving chat histories or scenarios where temporal relationships are meaningful.

You can only batch up to 20 episodes at a time. You can group episodes of different types (text, json, message) in the same batch.

See the [SDK reference](/sdk-reference/graph/add-batch) for details.

<CodeBlocks>

```python Python
episodes = [
    EpisodeData(
        data="This is an example text episode.",
        type="text"
    ),
    EpisodeData(
        data=json.dumps({"name": "Eric Clapton", "age": 78, "genre": "Rock"}),
        type="json"
    )
]

client.graph.add_batch(episodes=episodes, group_id=group_id)
```

```typescript TypeScript
const episodes: EpisodeData[] = [
    {
        data: "This is an example text episode.",
        type: "text"
    },
    {
        data: JSON.stringify({ foo: "bar", count: 42 }),
        type: "json"
    }
];
await client.graph.addBatch({ groupId, episodes });
```

```go Go
jsonData, _ := json.Marshal(map[string]interface{}{
    "foo": "bar",
    "baz": 42,
})

batchReq := &v2.AddDataBatchRequest{
    Episodes: []*v2.EpisodeData{
        {
            Data: "This is a text episode.",
            Type: v2.GraphDataTypeText,
        },
        {
            Data: string(jsonData),
            Type: v2.GraphDataTypeJSON,
        },
    },
    GroupID: &groupID,
}

resp, err := client.Graph.AddBatch(context.TODO(), batchReq)
if err != nil {
    log.Fatalf("Failed to add batch episodes: %v", err)
}
```
</CodeBlocks>

## Managing Your Data on the Graph

The `graph.add` method returns the [episode](/graphiti/graphiti/adding-episodes) that was created in the graph from adding that data. You can use this to maintain a mapping between your data and its corresponding episode in the graph and to delete specific data from the graph using the [delete episode](/deleting-data-from-the-graph#delete-an-episode) method.

---
title: Reading Data from the Graph
slug: reading-data-from-the-graph
---

Zep provides APIs to read Edges, Nodes, and Episodes from the graph. These elements can be retrieved individually using their `UUID`, or as lists associated with a specific `user_id` or `group_id`. The latter method returns all objects within the user's or group's graph.

Examples of each retrieval method are provided below.

## Reading Edges

<Tabs group="node-get">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

edge = client.graph.edge.get(edge_uuid)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const edge = client.graph.edge.get(edge_uuid);
```

</Tab>
</Tabs>

## Reading Nodes

<Tabs group="edge-get">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

node = client.graph.node.get_by_user(user_uuid)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const node = client.graph.node.get_by_user(user_uuid);
```

</Tab>
</Tabs>

## Reading Episodes

<Tabs group="episode-get">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

episode = client.graph.episode.get_by_group(group_uuid)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const episode = client.graph.episode.get_by_group(group_uuid);
```

</Tab>
</Tabs>

---
title: Searching the Graph
slug: searching-the-graph
---

Zep employs hybrid search, combining semantic similarity with BM25 full-text. Results are merged and [ranked](#reranking-search-results). Additional details can be found in the [SDK Reference](https://help.getzep.com/sdk-reference/graph/search).


The example below demonstrates a simple search.

<Tabs group="search">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

search_results = client.graph.search(
    user_id=user_id,
    query=query,
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const searchResults = await client.graph.search({
  userId: userId,
  query: query,
});
```

</Tab>
</Tabs>

> Read more about [chat message history search](/concepts/#using-memorysearch_sessions).

<Tip title="Best Practices" icon="magnifying-glass">
Keep queries short: they are truncated at 8,192 tokens. Long queries may increase latency without improving search quality. 
Break down complex searches into smaller, targeted queries. Use precise, contextual queries rather than generic ones
</Tip>

## Configurable Search Parameters
Zep allows several parameters to fine-tune search behavior:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `user_id` or `group_id` | **Required.** Specifies whether to search user-specific or group graphs | - |
| `scope` | Controls search [scope](#search-scopes) - either `"edges"` or `"nodes"`| `"edges"` |
| `reranker` | Method to [rerank](#reranking-search-results) results: `"rrf"`, `"mmr"`, `"node_distance"`, `"episode_mentions"`, or `"cross_encoder"`| `"rrf"` |
| `limit` | Maximum number of results to return | `10` |

## Search Scopes
Nodes are connection points in the graph that represent either:
- Chat history entities
- Business data added through the [Graph API](/adding-data-to-the-graph)

Each node maintains a summary of facts from its connections (edges), giving you a quick overview of things related to that node.

Edges represent individual connections between nodes, containing specific interactions or pieces of information. Edge search (the default) is best for finding specific details or conversations, while node search helps you understand the broader context around entities in your graph.

The example below demonstrates a node search.

<Tabs group="search">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

search_results = client.graph.search(
    group_id=group_id,
    query=query,
    scope="nodes",
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const searchResults = await client.graph.search({
  groupId: groupId,
  query: query,
  scope: "nodes",
});
```

</Tab>
</Tabs>

## Reranking Search Results
<a name="reciprocal-rank-fusion"></a>
Besides the default Reciprocal Rank Fusion (`rrf`) which combines results from semantic and BM25, Zep supports several reranking methods to improve search results:

- [Maximal Marginal Relevance ](#maximal-marginal-re-ranking)
- [Node Distance ](#node-distance)
- [Episode Mention ](#episode-mentions)
- [Cross Encoder ](#cross-encoder)

### Maximal Marginal Relevance Re-Ranking

<a name="maximal-marginal-re-ranking"></a>
Standard similarity searches often return highly similar top results, potentially limiting the information added to a prompt. `mmr` addresses this by re-ranking results to promote diversity, downranking similar results in favor of relevant but distinct alternatives.

> Required: `mmr_lambda` - tunes the balance between relevance and diversity

Example of MMR search:

<Tabs group="search">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

search_results = client.graph.search(
    user_id=user_id,
    query=query,
    reranker="mmr",
    mmr_lambda=0.5, # tune diversity vs relevance
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const searchResults = await client.graph.search({
  userId: userId,
  query: query,
  reranker: "mmr",
  mmrLambda: 0.5, // tune diversity vs relevance
});
```

</Tab>
</Tabs>

### Node Distance

`node_distance` re-ranks search results based on the number of hops between the search result and a center node. This can be useful for finding facts related to a specific node, such as a user or a topic.

> Required: `center_node_uuid` - UUID of the node to use as the center of the search

Example of Node Distance search:

<Tabs group="search">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

search_results = client.graph.search(
    user_id=user_id,
    query=query,
    reranker="node_distance",
    center_node_uuid=center_node_uuid,
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const searchResults = await client.graph.search({
  userId: userId,
  query: query,
  reranker: "node_distance",
  centerNodeUuid: centerNodeUuid,
});
```

</Tab>
</Tabs>

### Episode Mentions

`episode_mentions` re-ranks search results based on the number of times the node or edge has been mentioned in the chat history.

Example of Episode Mentions search:

<Tabs group="search">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

search_results = client.graph.search(
    user_id=user_id,
    query=query,
    reranker="episode_mentions",
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const searchResults = await client.graph.search({
  userId: userId,
  query: query,
  reranker: "episode_mentions",
});
```

</Tab>
</Tabs>

### Cross Encoder

`cross_encoder` re-ranks search results by using a specialized model that jointly analyzes the query and each search result together, providing more accurate relevance scoring than traditional methods that analyze them separately.

Example of Cross Encoder search:

<Tabs group="search">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

search_results = client.graph.search(
    user_id=user_id,
    query=query,
    reranker="cross_encoder",
)
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

const searchResults = await client.graph.search({
  userId: userId,
  query: query,
  reranker: "cross_encoder",
});
```

</Tab>
</Tabs>

---
title: Deleting Data from the Graph
slug: deleting-data-from-the-graph
---
 


## Delete an Edge

Here's how to delete an edge from a graph:

<Tabs group="deleting-edges">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

client.graph.edge.delete(uuid_="your_edge_uuid")
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

await client.graph.edge.delete("your_edge_uuid");
```

</Tab>
</Tabs>

Note that when you delete an edge, it never deletes the associated nodes, even if it means there will be a node with no edges. And currently, nodes with no edges will not appear in the graph explorer, but they will still exist in the graph and be retrievable in memory.

## Delete an Episode

<Note>
Deleting an episode does not regenerate the names or summaries of nodes shared with other episodes. This episode information may still exist within these nodes. If an episode invalidates a fact, and the episode is deleted, the fact will remain marked as invalidated.
</Note>

When you delete an [episode](/graphiti/graphiti/adding-episodes), it will delete all the edges associated with it, and it will delete any nodes that are only attached to that episode. Nodes that are also attached to another episode will not be deleted.

Here's how to delete an episode from a graph:

<Tabs group="deleting-episodes">

<Tab title="Python" group-key="python">

```python
from zep_cloud.client import Zep

client = Zep(
    api_key=API_KEY,
)

client.graph.episode.delete(uuid_="episode_uuid")
```

</Tab>

<Tab title="TypeScript" group-key="ts">

```typescript
import { ZepClient } from "@getzep/zep-cloud";

const client = new ZepClient({
  apiKey: API_KEY,
});

await client.graph.episode.delete("episode_uuid");
```

</Tab>
</Tabs>

## Delete a Node

This feature is coming soon.


---
title: Check Data Ingestion Status
slug: cookbook/check-data-ingestion-status
---

Data added to Zep is processed asynchronously and can take a few seconds to a few minutes to finish processing. In this recipe, we show how to check whether a given data upload request (also known as an [Episode](/graphiti/graphiti/adding-episodes)) is finished processing by polling Zep with the `graph.episode.get` method.

First, let's create a user:

<CodeBlocks>
```python
import os
import uuid
import time
from dotenv import find_dotenv, load_dotenv
from zep_cloud.client import Zep

load_dotenv(dotenv_path=find_dotenv())

client = Zep(api_key=os.environ.get("ZEP_API_KEY"))
uuid_value = uuid.uuid4().hex[:4]
user_id = "-" + uuid_value
client.user.add(
    user_id=user_id,
    first_name = "John",
    last_name = "Doe",
    email="john.doe@example.com"
)
```
```typescript
import { ZepClient } from "@getzep/zep-cloud";
import * as dotenv from "dotenv";
import { v4 as uuidv4 } from 'uuid';

// Load environment variables
dotenv.config();

const client = new ZepClient({ apiKey: process.env.ZEP_API_KEY || "" });
const uuidValue = uuidv4().substring(0, 4);
const userId = "-" + uuidValue;

async function main() {
  // Add user
  await client.user.add({
    userId: userId,
    firstName: "John",
    lastName: "Doe",
    email: "john.doe@example.com"
  });
```
```go
package main

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/getzep/zep-go/v2"
	zepclient "github.com/getzep/zep-go/v2/client"
	"github.com/getzep/zep-go/v2/option"
	"github.com/google/uuid"
	"github.com/joho/godotenv"
)

func main() {
	// Load .env file
	err := godotenv.Load()
	if err != nil {
		fmt.Println("Warning: Error loading .env file:", err)
		// Continue execution as environment variables might be set in the system
	}

	// Get API key from environment variable
	apiKey := os.Getenv("ZEP_API_KEY")
	if apiKey == "" {
		fmt.Println("ZEP_API_KEY environment variable is not set")
		return
	}

	// Initialize Zep client
	client := zepclient.NewClient(
		option.WithAPIKey(apiKey),
	)

	// Create a UUID
	uuidValue := strings.ToLower(uuid.New().String()[:4])

	// Create user ID
	userID := "-" + uuidValue

	// Create context
	ctx := context.Background()

	// Add a user
	userRequest := &zep.CreateUserRequest{
		UserID:    zep.String(userID),
		FirstName: zep.String("John"),
		LastName:  zep.String("Doe"),
		Email:     zep.String("john.doe@example.com"),
	}
	_, err = client.User.Add(ctx, userRequest)
	if err != nil {
		fmt.Printf("Error creating user: %v\n", err)
		return
	}
```
</CodeBlocks>

Now, let's add some data and immediately try to search for that data; because data added to Zep is processed asynchronously and can take a few seconds to a few minutes to finish processing, our search results do not have the data we just added:

<CodeBlocks>
```python
episode = client.graph.add(
    user_id=user_id,
    type="text", 
    data="The user is an avid fan of Eric Clapton"
)

search_results = client.graph.search(
    user_id=user_id,
    query="Eric Clapton",
    scope="nodes",
    limit=1,
    reranker="cross_encoder",
)

print(search_results.nodes)
```
```typescript
  // Add episode to graph
  const episode = await client.graph.add({
    userId: userId,
    type: "text",
    data: "The user is an avid fan of Eric Clapton"
  });

  // Search for nodes related to Eric Clapton
  const searchResults = await client.graph.search({
    userId: userId,
    query: "Eric Clapton",
    scope: "nodes",
    limit: 1,
    reranker: "cross_encoder"
  });

  console.log(searchResults.nodes);
```
```go
	// Add a new episode to the graph
	episode, err := client.Graph.Add(ctx, &zep.AddDataRequest{
		GroupID: zep.String(userID),
		Type:    zep.GraphDataTypeText.Ptr(),
		Data:    zep.String("The user is an avid fan of Eric Clapton"),
	})
	if err != nil {
		fmt.Printf("Error adding episode to graph: %v\n", err)
		return
	}

	// Search for the data
	searchResults, err := client.Graph.Search(ctx, &zep.GraphSearchQuery{
		UserID:  zep.String(userID),
		Query:   "Eric Clapton",
		Scope:   zep.GraphSearchScopeNodes.Ptr(),
		Limit:   zep.Int(1),
		Reranker: zep.RerankerCrossEncoder.Ptr(),
	})
	if err != nil {
		fmt.Printf("Error searching graph: %v\n", err)
		return
	}

	fmt.Println(searchResults.Nodes)
```
</CodeBlocks>

```text
None
```

We can check the status of the episode to see when it has finished processing, using the episode returned from the `graph.add` method and the `graph.episode.get` method:

<CodeBlocks>
```python
while True:
    episode = client.graph.episode.get(
        uuid_=episode.uuid_,
    )
    if episode.processed:
        print("Episode processed successfully")
        break
    print("Waiting for episode to process...")
    time.sleep(1)
```
```typescript
  // Check if episode is processed
  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
  
  let processedEpisode = await client.graph.episode.get(episode.uuid);
  
  while (!processedEpisode.processed) {
    console.log("Waiting for episode to process...");
    await sleep(1000); // Sleep for 1 second
    processedEpisode = await client.graph.episode.get(episode.uuid);
  }
  
  console.log("Episode processed successfully");
```
```go
	// Wait for the episode to be processed
	for {
		episodeStatus, err := client.Graph.Episode.Get(
			ctx,
			episode.UUID,
		)
		if err != nil {
			fmt.Printf("Error getting episode: %v\n", err)
			return
		}

		if episodeStatus.Processed != nil && *episodeStatus.Processed {
			fmt.Println("Episode processed successfully")
			break
		}

		fmt.Println("Waiting for episode to process...")
		time.Sleep(1 * time.Second)
	}
```
</CodeBlocks>

```text
Waiting for episode to process...
Waiting for episode to process...
Waiting for episode to process...
Waiting for episode to process...
Waiting for episode to process...
Episode processed successfully
```

Now that the episode has finished processing, we can search for the data we just added, and this time we get a result:

<CodeBlocks>
```python
search_results = client.graph.search(
    user_id=user_id,
    query="Eric Clapton",
    scope="nodes",
    limit=1,
    reranker="cross_encoder",
)

print(search_results.nodes)
```
```typescript
  // Search again after processing
  const finalSearchResults = await client.graph.search({
    userId: userId,
    query: "Eric Clapton",
    scope: "nodes",
    limit: 1,
    reranker: "cross_encoder"
  });

  console.log(finalSearchResults.nodes);
}

// Execute the main function
main().catch(error => console.error("Error:", error));
```
```go
	// Search again after processing
	searchResults, err = client.Graph.Search(ctx, &zep.GraphSearchQuery{
		UserID:  zep.String(userID),
		Query:   "Eric Clapton",
		Scope:   zep.GraphSearchScopeNodes.Ptr(),
		Limit:   zep.Int(1),
		Reranker: zep.RerankerCrossEncoder.Ptr(),
	})
	if err != nil {
		fmt.Printf("Error searching graph: %v\n", err)
		return
	}

	fmt.Println(searchResults.Nodes)
}
```
</CodeBlocks>

```text
[EntityNode(attributes={'category': 'Music', 'labels': ['Entity', 'Preference']}, created_at='2025-04-05T00:17:59.66565Z', labels=['Entity', 'Preference'], name='Eric Clapton', summary='The user is an avid fan of Eric Clapton.', uuid_='98808054-38ad-4cba-ba07-acd5f7a12bc0', graph_id='6961b53f-df05-48bb-9b8d-b2702dd72045')]
```

import uuid
from zep_cloud import Message
from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel, EntityBoolean
from zep_cloud import EntityEdgeSourceTarget
from pydantic import Field

class Restaurant(EntityModel):
    """
    Represents a specific restaurant.
    """
    cuisine_type: EntityText = Field(description="The cuisine type of the restaurant, for example: American, Mexican, Indian, etc.", default=None)
    dietary_accommodation: EntityText = Field(description="The dietary accommodation of the restaurant, if any, for example: vegetarian, vegan, etc.", default=None)

class RestaurantVisit(EdgeModel):
    """
    Represents the fact that the user visited a restaurant.
    """
    restaurant_name: EntityText = Field(description="The name of the restaurant the user visited", default=None)

class DietaryPreference(EdgeModel):
    """
    Represents the fact that the user has a dietary preference or dietary restriction.
    """
    preference_type: EntityText = Field(description="Preference type of the user: anything, vegetarian, vegan, peanut allergy, etc.", default=None)
    allergy: EntityBoolean = Field(description="Whether this dietary preference represents a user allergy: True or false", default=None)

client.graph.set_ontology(
    entities={
        "Restaurant": Restaurant,
    },
    edges={
        "RESTAURANT_VISIT": (
            RestaurantVisit,
            [EntityEdgeSourceTarget(source="User", target="Restaurant")]
        ),
        "DIETARY_PREFERENCE": (
            DietaryPreference,
            [EntityEdgeSourceTarget(source="User")]
        ),
    }
)

messages_session1 = [
    Message(content="Take me to a lunch place", role_type="user", role="John Doe"),
    Message(content="How about Panera Bread, Chipotle, or Green Leaf Cafe, which are nearby?", role_type="assistant", role="Assistant"),
    Message(content="Do any of those have vegetarian options? I’m vegetarian", role_type="user", role="John Doe"),
    Message(content="Yes, Green Leaf Cafe has vegetarian options", role_type="assistant", role="Assistant"),
    Message(content="Let’s go to Green Leaf Cafe", role_type="user", role="John Doe"),
    Message(content="Navigating to Green Leaf Cafe", role_type="assistant", role="Assistant"),
]

messages_session2 = [
    Message(content="Take me to dessert", role_type="user", role="John Doe"),
    Message(content="How about getting some ice cream?", role_type="assistant", role="Assistant"),
    Message(content="I can't have ice cream, I'm lactose intolerant, but I'm craving a chocolate chip cookie", role_type="user", role="John Doe"),
    Message(content="Sure, there's Insomnia Cookies nearby.", role_type="assistant", role="Assistant"),
    Message(content="Perfect, let's go to Insomnia Cookies", role_type="user", role="John Doe"),
    Message(content="Navigating to Insomnia Cookies.", role_type="assistant", role="Assistant"),
]

user_id = f"user-{uuid.uuid4()}"
client.user.add(user_id=user_id, first_name="John", last_name="Doe", email="john.doe@example.com")

session1_id = f"session-{uuid.uuid4()}"
session2_id = f"session-{uuid.uuid4()}"
client.memory.add_session(session_id=session1_id, user_id=user_id)
client.memory.add_session(session_id=session2_id, user_id=user_id)

client.memory.add(session_id=session1_id, messages=messages_session1, ignore_roles=["assistant"])
client.memory.add(session_id=session2_id, messages=messages_session2, ignore_roles=["assistant"])


---
title: Add User Specific Business Data to User Graphs
slug: cookbook/how-to-add-user-specific-business-data-to-user-graphs
---

This guide demonstrates how to add user-specific business data to a user's knowledge graph. We'll create a user, fetch their business data, and add it to their graph.

First, we will initialize our client and create a new user:

```python
# Initialize the Zep client
zep_client = AsyncZep(api_key=API_KEY)

# Add one example user
user_id_zep = uuid.uuid4().hex
await zep_client.user.add(
    user_id=user_id_zep,
    email="cookbook@example.com"
)
```

Then, we will fetch and format the user's business data. Note that the functionality to fetch a users business data will depend on your codebase. 

Also note that you could make your Zep user IDs equal to whatever internal user IDs you use to make things easier to manage. Generally, Zep user IDs, session IDs, Group IDs, etc. can be arbitrary strings, and can map to your app's data schema.

```python
# Define the function to fetch user business data
async def get_user_business_data(user_id_business):
    # This function returns JSON data for the given user
    # This would vary based on your codebase
    return {}

# Placeholder for business user id
user_id_business = "placeholder_user_id"  # This would vary based on your codebase

# Retrieve the user-specific business data
user_data_json = await get_user_business_data(user_id_business)

# Convert the business data to a string
json_string = json.dumps(user_data_json)
```
Lastly, we will add the formatted data to the user's graph using the [graph API](/adding-data-to-the-graph):

```python
# Add the JSON data to the user's graph
await zep_client.graph.add(
    user_id=user_id_zep,
    type="json",
    data=json_string,
)
```
Here, we use `type="json"`, but the graph API also supports `type="text"` and `type="message"`. The `type="text"` option is useful for adding background information that is in unstructured text such as internal documents or web copy. The `type="message"` option is useful for adding data that is in a message format but is not your user's chat history, such as emails. [Read more about this here](/adding-data-to-the-graph).

Also, note that when adding data to the graph, you should consider the size of the data you are adding and our payload limits. [Read more about this here](/docs/performance/performance-best-practices#optimizing-memory-operations).

You have now successfully added user-specific business data to a user's knowledge graph, which can be used alongside chat history to create comprehensive user memory.


---
title: Share Memory Across Users Using Group Graphs
slug: cookbook/how-to-share-memory-across-users-using-group-graphs
---

In this recipe, we will demonstrate how to share memory across different users by utilizing group graphs. We will set up a user session, add group-specific data, and integrate the OpenAI client to show how to use both user and group memory to enhance the context of a chatbot.

First, we initialize the Zep client, create a user, and create a session:

```python
# Initialize the Zep client
zep_client = AsyncZep(api_key="YOUR_API_KEY")  # Ensure your API key is set appropriately

# Add one example user
user_id = uuid.uuid4().hex
await zep_client.user.add(
    user_id=user_id,
    email="cookbook@example.com"
)

# Create a new session for the user
session_id = uuid.uuid4().hex
await zep_client.memory.add_session(
    session_id=session_id,
    user_id=user_id,
)
```

Next, we create a new group and add structured business data to the graph, in the form of a JSON string. This step uses the [groups API](/groups) and the [graph API](/adding-data-to-the-graph):

```python
group_id = uuid.uuid4().hex
await zep_client.group.add(group_id=group_id)

product_json_data = [
    {
        "type": "Sedan",
        "gas_mileage": "25 mpg",
        "maker": "Toyota"
    },
    # ... more cars
]

json_string = json.dumps(product_json_data)
await zep_client.graph.add(
    group_id=group_id,
    type="json",
    data=json_string,
)
```

Finally, we initialize the OpenAI client and define a `chatbot_response` function that retrieves user and group memory, constructs a system/developer message, and generates a contextual response. This leverages the [memory API](/concepts#using-memoryget), [graph API](/searching-the-graph), and the OpenAI chat completions endpoint.

```python
# Initialize the OpenAI client
oai_client = OpenAI()

async def chatbot_response(user_message, session_id):
    # Retrieve user memory
    user_memory = await zep_client.memory.get(session_id)

    # Search the group graph using the user message as the query
    results = await zep_client.graph.search(group_id=group_id, query=user_message, scope="edges")
    relevant_group_edges = results.edges
    product_context_string = "Below are some facts related to our car inventory that may help you respond to the user: \n"
    for edge in relevant_group_edges:
        product_context_string += f"{edge.fact}\n"

    # Combine context strings for the developer message
    developer_message = f"You are a helpful chat bot assistant for a car sales company. Answer the user's message while taking into account the following background information:\n{user_memory.context}\n{product_context_string}"

    # Generate a response using the OpenAI API
    completion = oai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": developer_message},
            {"role": "user", "content": user_message}
        ]
    )
    response = completion.choices[0].message

    # Add the conversation to memory
    messages = [
        Message(role="user", role_type="user", content=user_message),
        Message(role="assistant", role_type="assistant", content=response)
    ]
    await zep_client.memory.add(session_id, messages=messages)

    return response
```

This recipe demonstrated how to share memory across users by utilizing group graphs with Zep. We set up user sessions, added structured group data, and integrated the OpenAI client to generate contextual responses, providing a robust approach to memory sharing across different users.


---
title: Get Most Relevant Facts for an Arbitrary Query
slug: cookbook/how-to-get-most-relevant-facts-for-an-arbitrary-query
---

In this recipe, we demonstrate how to retrieve the most relevant facts from the knowledge graph using an arbitrary search query.

First, we perform a [search](/searching-the-graph) on the knowledge graph using a sample query:

```python
zep_client = AsyncZep(api_key=API_KEY)
results = await client.graph.search(user_id="some user_id", query="Some search query", scope="edges")
```

Then, we get the edges from the search results and construct our fact list. We also include the temporal validity data to each fact string:

```python
# Build list of formatted facts
relevant_edges = results.edges
formatted_facts = []
for edge in relevant_edges:
    valid_at = edge.valid_at if edge.valid_at is not None else "date unknown"
    invalid_at = edge.invalid_at if edge.invalid_at is not None else "present"
    formatted_fact = f"{edge.fact} (Date range: {valid_at} - {invalid_at})"
    formatted_facts.append(formatted_fact)

# Print the results
print("\nFound facts:")
for fact in formatted_facts:
    print(f"- {fact}")
```

We demonstrated how to retrieve the most relevant facts for an arbitrary query using the Zep client. Adjust the query and parameters as needed to tailor the search for your specific use case.


---
title: Find Facts Relevant to a Specific Node
slug: cookbook/how-to-find-facts-relevant-to-a-specific-node
---

Below, we will go through how to retrieve facts which are related to a specific node in a Zep knowledge graph. First, we will go through some methods for determining the UUID of the node you are interested in. Then, we will go through some methods for retrieving the facts related to that node.

If you are interested in the user's node specifically, we have a convenience method that [returns the user's node](/users#get-the-user-node) which includes the UUID.

An easy way to determine the UUID for other nodes is to use the graph explorer in the [Zep Web app](https://app.getzep.com/).

You can also programmatically retrieve all the nodes for a given user using our [get nodes by user API](/sdk-reference/graph/node/get-by-user-id), and then manually examine the nodes and take note of the UUID of the node of interest:

```python
# Initialize the Zep client
zep_client = AsyncZep(api_key=API_KEY)
nodes = await zep_client.graph.node.get_by_user_id(user_id="some user ID")
print(nodes)
```
```python
center_node_uuid = "your chosen center node UUID"
```

Lastly, if your user has a lot of nodes to look through, you can narrow down the search by only looking at the nodes relevant to a specific query, using our [graph search API](/searching-the-graph):

```python
results = await zep_client.graph.search(
    user_id="some user ID",
    query="shoe", # To help narrow down the nodes you have to manually search
    scope="nodes"
)
relevant_nodes = results.nodes
print(relevant_nodes)
```
```python
center_node_uuid = "your chosen center node UUID"
```

The most straightforward way to get facts related to your node is to retrieve all facts that are connected to your chosen node using the [get edges by user API](/sdk-reference/graph/edge/get-by-user-id):

```python
edges = await zep_client.graph.edge.get_by_user_id(user_id="some user ID")
connected_edges = [edge for edge in edges if edge.source_node_uuid == center_node_uuid or edge.target_node_uuid == center_node_uuid]
relevant_facts = [edge.fact for edge in connected_edges]
```

You can also retrieve facts relevant to your node by using the [graph search API](/searching-the-graph) with the node distance re-ranker:

```python
results = await zep_client.graph.search(
    user_id="some user ID",
    query="some query",
    reranker="node_distance",
    center_node_uuid=center_node_uuid,
)
relevant_edges = results.edges
relevant_facts = [edge.fact for edge in relevant_edges]
```

In this recipe, we went through how to retrieve facts which are related to a specific node in a Zep knowledge graph. We first went through some methods for determining the UUID of the node you are interested in. Then, we went through some methods for retrieving the facts related to that node.
