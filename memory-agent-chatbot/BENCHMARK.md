# BENCHMARK.md — Lab 17: Multi-Memory Agent Benchmark

## Overview

Benchmark comparing **no-memory** vs **with-memory** agent across 10 multi-turn
conversations covering all required test categories:

- **Profile recall** (2 tests)
- **Conflict update** (2 tests)
- **Episodic recall** (2 tests)
- **Semantic retrieval** (2 tests)
- **Token budget / trim** (1 test)
- **Combined memory** (1 test)

---

## Results Summary

| # | Scenario | Category | No-Memory Result | With-Memory Result | Pass? |
|---|----------|----------|------------------|---------------------|-------|
| 1 | Profile recall: remember user name after multiple  | profile_recall | Xin lỗi, nhưng mình không có thông tin về tên của bạn. Bạn c | Có chứ, tên bạn là Linh! Bạn đang học ngành Computer Science | ✅ Pass |
| 2 | Conflict update: correct an allergy fact | conflict_update | Mình không có thông tin cụ thể về tình trạng sức khỏe của bạ | Bạn bị dị ứng đậu nành. Nếu bạn cần gợi ý về món ăn hoặc thự | ✅ Pass |
| 3 | Episodic recall: remember a past debugging experie | episodic_recall | Mình không có thông tin cụ thể về cách bạn đã khắc phục lỗi  | Lần trước bạn gặp lỗi với Docker container không kết nối đượ | ✅ Pass |
| 4 | Semantic retrieval: retrieve relevant knowledge ch | semantic_retrieval | LangGraph là một công cụ hoặc nền tảng hỗ trợ trong việc xây | LangGraph là một framework dùng để xây dựng các workflows ag | ✅ Pass |
| 5 | Profile recall: remember multiple user facts | profile_recall | Tôi nhớ rằng bạn đã hỏi nhiều điều về cuộc sống hàng ngày và | Bạn tên là Minh, 22 tuổi và sống ở Hà Nội. Bạn thích lập trì | ✅ Pass |
| 6 | Conflict update: user changes job | conflict_update | Mình không có thông tin cụ thể về nơi bạn làm việc. Nếu bạn  | Bạn đang làm việc full-time tại VNG. Nếu bạn muốn chia sẻ th | ✅ Pass |
| 7 | Episodic recall: finished coding task | episodic_recall | Bạn đã deploy project lên Heroku. Nếu bạn cần hỗ trợ gì về d | Bạn đã deploy project lên Railway. Nếu bạn có bất kỳ câu hỏi | ✅ Pass |
| 8 | Semantic retrieval: technical concept search | semantic_retrieval | RAG, hay còn gọi là Retrieval-Augmented Generation, là một p | RAG (Retrieval-Augmented Generation) hoạt động theo ba bước  | ✅ Pass |
| 9 | Token budget: agent handles long conversation with | trim_token_budget | Xin lỗi, nhưng tôi không nhớ tên của bạn. Bạn có thể cho tôi | Có, tên của bạn là Hoa! Nếu có điều gì bạn muốn chia sẻ hoặc | ✅ Pass |
| 10 | Combined: profile + episodes + semantic in one res | combined | Dựa trên kinh nghiệm của bạn về việc di chuyển cơ sở dữ liệu | Với kinh nghiệm migrate database từ MySQL sang PostgreSQL và | ✅ Pass |

**Score: 10/10 tests passed**

---

## Detailed Results

### Test #1: Profile recall: remember user name after multiple turns

**Category:** profile_recall
**Description:** Agent should remember user's name (Linh) after 6+ turns
**Expected keyword:** `Linh`

**No-memory response:**
> Xin lỗi, nhưng mình không có thông tin về tên của bạn. Bạn có thể cho mình biết tên của bạn được không?

**With-memory response:**
> Có chứ, tên bạn là Linh! Bạn đang học ngành Computer Science ở VinUni. Nếu bạn cần hỗ trợ gì thêm, hãy cho mình biết nhé!

**Result:** ✅ PASS

**Token usage (with-memory):** ~693 tokens

**Memory status after test:**
- Short-term: 10 messages
- Profile facts: {"name": "Linh", "field_of_study": "Computer Science", "university": "VinUni"}
- Episodes: 1 recorded
- Semantic docs: 4

---

### Test #2: Conflict update: correct an allergy fact

**Category:** conflict_update
**Description:** Agent should update allergy to đậu nành, not keep sữa bò
**Expected keyword:** `đậu nành`

**No-memory response:**
> Mình không có thông tin cụ thể về tình trạng sức khỏe của bạn. Tuy nhiên, nếu bạn có triệu chứng như ngứa, phát ban, hắt hơi hay khó thở, có thể bạn đang bị dị ứng. Để xác định chính xác bạn bị dị ứng

**With-memory response:**
> Bạn bị dị ứng đậu nành. Nếu bạn cần gợi ý về món ăn hoặc thực phẩm nào an toàn cho bạn, hãy cho mình biết nhé!

**Result:** ✅ PASS

**Token usage (with-memory):** ~482 tokens

**Memory status after test:**
- Short-term: 8 messages
- Profile facts: {"allergies": "đậu nành"}
- Episodes: 0 recorded
- Semantic docs: 0

---

### Test #3: Episodic recall: remember a past debugging experience

**Category:** episodic_recall
**Description:** Agent recalls the Docker debugging resolution from episodic memory
**Expected keyword:** `service name`

**No-memory response:**
> Mình không có thông tin cụ thể về cách bạn đã khắc phục lỗi Docker trước đó. Nếu bạn có thể cung cấp thêm chi tiết về lỗi mà bạn gặp phải, mình có thể giúp bạn tìm ra giải pháp hoặc nhắc lại những phư

**With-memory response:**
> Lần trước bạn gặp lỗi với Docker container không kết nối được đến database. Bạn đã khắc phục vấn đề bằng cách sử dụng Docker service name thay vì localhost để đảm bảo các container có thể giao tiếp vớ

**Result:** ✅ PASS

**Token usage (with-memory):** ~254 tokens

**Memory status after test:**
- Short-term: 8 messages
- Profile facts: {}
- Episodes: 4 recorded
- Semantic docs: 3

---

### Test #4: Semantic retrieval: retrieve relevant knowledge chunk

**Category:** semantic_retrieval
**Description:** Agent retrieves the LangGraph knowledge chunk from semantic memory
**Expected keyword:** `graph`

**No-memory response:**
> LangGraph là một công cụ hoặc nền tảng hỗ trợ trong việc xây dựng và phát triển các ứng dụng liên quan đến ngôn ngữ tự nhiên và trí tuệ nhân tạo. Nó thường được sử dụng để tạo ra các mô hình ngôn ngữ,

**With-memory response:**
> LangGraph là một framework dùng để xây dựng các workflows agent dạng graph. Nó cho phép bạn định nghĩa các trạng thái (state), các nút (nodes), và các cạnh (edges) để tạo ra các quy trình xử lý phức t

**Result:** ✅ PASS

**Token usage (with-memory):** ~95 tokens

**Memory status after test:**
- Short-term: 2 messages
- Profile facts: {}
- Episodes: 0 recorded
- Semantic docs: 4

---

### Test #5: Profile recall: remember multiple user facts

**Category:** profile_recall
**Description:** Agent recalls name, age, location, and programming preferences
**Expected keyword:** `Minh`

**No-memory response:**
> Tôi nhớ rằng bạn đã hỏi nhiều điều về cuộc sống hàng ngày và những sở thích của mình. Bạn có vẻ thích khám phá kiến thức mới và luôn tìm kiếm những thông tin hữu ích. Nếu có điều gì cụ thể bạn muốn tô

**With-memory response:**
> Bạn tên là Minh, 22 tuổi và sống ở Hà Nội. Bạn thích lập trình, đặc biệt là với ngôn ngữ Python và Rust. Bạn thường sử dụng VS Code để lập trình. Nếu bạn có thêm điều gì muốn chia sẻ hay hỏi, mình rất

**Result:** ✅ PASS

**Token usage (with-memory):** ~208 tokens

**Memory status after test:**
- Short-term: 8 messages
- Profile facts: {"name": "Minh", "age": "22", "location": "Hà Nội", "interests": "lập trình Python", "tools": "VS Code", "favorite_languages": "Python and Rust", "preferred_ide": "VS Code"}
- Episodes: 0 recorded
- Semantic docs: 0

---

### Test #6: Conflict update: user changes job

**Category:** conflict_update
**Description:** Agent updates workplace from FPT to VNG
**Expected keyword:** `VNG`

**No-memory response:**
> Mình không có thông tin cụ thể về nơi bạn làm việc. Nếu bạn muốn chia sẻ, mình có thể ghi nhớ để hỗ trợ bạn tốt hơn trong các cuộc trò chuyện sau.

**With-memory response:**
> Bạn đang làm việc full-time tại VNG. Nếu bạn muốn chia sẻ thêm về công việc hoặc trải nghiệm của mình tại VNG, mình rất vui được nghe!

**Result:** ✅ PASS

**Token usage (with-memory):** ~168 tokens

**Memory status after test:**
- Short-term: 8 messages
- Profile facts: {"job": "full-time at VNG", "company": "FPT Software", "previous_job": "FPT Software"}
- Episodes: 1 recorded
- Semantic docs: 0

---

### Test #7: Episodic recall: finished coding task

**Category:** episodic_recall
**Description:** Agent recalls the deployment platform from episodic memory
**Expected keyword:** `Railway`

**No-memory response:**
> Bạn đã deploy project lên Heroku. Nếu bạn cần hỗ trợ gì về dự án hoặc Heroku, hãy cho mình biết nhé!

**With-memory response:**
> Bạn đã deploy project lên Railway. Nếu bạn có bất kỳ câu hỏi nào về quá trình deploy hoặc muốn chia sẻ thêm về trải nghiệm của bạn, hãy cho mình biết nhé!

**Result:** ✅ PASS

**Token usage (with-memory):** ~230 tokens

**Memory status after test:**
- Short-term: 8 messages
- Profile facts: {}
- Episodes: 4 recorded
- Semantic docs: 1

---

### Test #8: Semantic retrieval: technical concept search

**Category:** semantic_retrieval
**Description:** Agent retrieves the RAG knowledge chunk and explains it
**Expected keyword:** `retrieval`

**No-memory response:**
> RAG, hay còn gọi là Retrieval-Augmented Generation, là một phương pháp kết hợp giữa tìm kiếm thông tin và sinh văn bản. Nó hoạt động theo các bước chính sau:

1. **Tìm kiếm thông tin**: Khi nhận được 

**With-memory response:**
> RAG (Retrieval-Augmented Generation) hoạt động theo ba bước chính:

1. **Indexing**: Các tài liệu được chuyển đổi thành embeddings, tức là các biểu diễn số học giúp máy tính hiểu và phân loại nội dung

**Result:** ✅ PASS

**Token usage (with-memory):** ~173 tokens

**Memory status after test:**
- Short-term: 2 messages
- Profile facts: {}
- Episodes: 0 recorded
- Semantic docs: 4

---

### Test #9: Token budget: agent handles long conversation without overflow

**Category:** trim_token_budget
**Description:** After 12+ turns, agent still recalls user's name within token budget
**Expected keyword:** `Hoa`

**No-memory response:**
> Xin lỗi, nhưng tôi không nhớ tên của bạn. Bạn có thể cho tôi biết tên của bạn không?

**With-memory response:**
> Có, tên của bạn là Hoa! Nếu có điều gì bạn muốn chia sẻ hoặc hỏi thêm, hãy cho mình biết nhé!

**Result:** ✅ PASS

**Token usage (with-memory):** ~5373 tokens

**Memory status after test:**
- Short-term: 10 messages
- Profile facts: {"name": "Hoa"}
- Episodes: 0 recorded
- Semantic docs: 12

---

### Test #10: Combined: profile + episodes + semantic in one response

**Category:** combined
**Description:** Agent combines profile (backend dev), episode (migration), and semantic (PostgreSQL docs) for a contextual answer
**Expected keyword:** `PostgreSQL`

**No-memory response:**
> Dựa trên kinh nghiệm của bạn về việc di chuyển cơ sở dữ liệu và vai trò backend developer, dưới đây là một số lĩnh vực mà bạn có thể tìm hiểu thêm về PostgreSQL:

1. **Tối ưu hóa hiệu suất**: Nghiên c

**With-memory response:**
> Với kinh nghiệm migrate database từ MySQL sang PostgreSQL và vai trò của bạn là backend developer, đây là một số lĩnh vực bạn có thể tìm hiểu thêm về PostgreSQL:

1. **Advanced Features**: Tìm hiểu về

**Result:** ✅ PASS

**Token usage (with-memory):** ~482 tokens

**Memory status after test:**
- Short-term: 6 messages
- Profile facts: {"name": "Đức", "job": "backend developer", "recent_experience": "migrate database from MySQL to PostgreSQL"}
- Episodes: 2 recorded
- Semantic docs: 3

---

## Token Budget Analysis

| # | Scenario | Total Tokens (with-memory) |
|---|----------|---------------------------|
| 1 | Profile recall: remember user name after | ~693 |
| 2 | Conflict update: correct an allergy fact | ~482 |
| 3 | Episodic recall: remember a past debuggi | ~254 |
| 4 | Semantic retrieval: retrieve relevant kn | ~95 |
| 5 | Profile recall: remember multiple user f | ~208 |
| 6 | Conflict update: user changes job | ~168 |
| 7 | Episodic recall: finished coding task | ~230 |
| 8 | Semantic retrieval: technical concept se | ~173 |
| 9 | Token budget: agent handles long convers | ~5373 |
| 10 | Combined: profile + episodes + semantic  | ~482 |

**Memory token budget:** 3000 tokens
**Short-term window:** 10 messages
