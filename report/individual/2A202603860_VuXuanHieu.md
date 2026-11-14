# Báo cáo cá nhân Day 06 — Vũ Xuân Hiếu

**MSSV** 2A202603860 · **Lớp** L3B · **Ngày chạy** 14/11/2026, giờ Việt Nam

## Dữ liệu và pipeline

Bộ dữ liệu là Quy chế đào tạo đại học ĐHQGHN ban hành kèm Quyết định 3626/QĐ-ĐHQGHN ngày 21/10/2022. File scan của người học có 53 trang PDF, trong đó trang 1 là quyết định ban hành. Phần quy chế ở trang PDF 2–53. Bản có lớp chữ lấy từ kho văn bản chính thức chứa riêng 52 trang quy chế, đánh số 1–52. Bản chạy dùng cả 52 trang này, tổng cộng 92.811 ký tự chuẩn hóa. [Manifest nguồn, checksum và thống kê từng trang](../../data/manifest.json)

PyMuPDF đọc từng trang theo thứ tự lớp chữ. Pipeline bỏ số trang đứng riêng, chuẩn hóa Unicode NFC và khoảng trắng, nối dòng bị ngắt do trình bày, nhận diện tiêu đề chương, điều và mục liệt kê. Phạm vi chương và điều được duy trì qua ngắt trang. Tất cả 52 trang đều trích xuất được chữ. Công thức ở trang 6–7 và một số bảng có thể bị phẳng hoặc sai thứ tự khi đọc lớp chữ. Bộ câu hỏi sử dụng bằng chứng dạng văn xuôi và các mệnh đề đọc được. Corpus dùng phần Quy chế do ĐHQGHN ban hành và công bố. Bài lab phân loại phần Quy chế là chính văn hành chính phục vụ quản lý đào tạo, dựa trên thẩm quyền của ĐHQGHN tại thời điểm ban hành, hình thức quy chế ban hành kèm quyết định và phạm vi áp dụng ghi tại Điều 1. Manifest dẫn khoản 2 Điều 15 Luật Sở hữu trí tuệ, khoản 2 Điều 8 của văn bản hướng dẫn và căn cứ về cơ quan ban hành, thẩm quyền và loại văn bản. PDF, nguyên văn trace, trọng số và index được lưu cục bộ trong `.local/`. Người chấm có thể tải bản nguồn theo manifest và tái tạo bằng chứng từ offsets.

Model intfloat/multilingual-e5-small, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, vector 384 chiều, ONNX INT8 trên CPU, FastEmbed 0.9.1, ONNX Runtime 1.32.0, PyMuPDF 1.27.2.3 và qdrant-client 1.20.0. Embedding dùng tiền tố `query: ` và `passage: `. Qdrant local lưu hai collection, tìm cosine exact. Chi phí dịch vụ **0 USD**. Chi phí máy và điện chưa được đo. [Lệnh và phiên bản tái lập](../../README.md) · [Thông tin lần chạy](../../results/dev_selection.json)

Mỗi chunk có ID ổn định, ID tài liệu, URL nguồn, trang vật lý, offsets, danh sách chương và danh sách điều. Một đoạn tiêu đề chương có thể có danh sách điều rỗng vì nằm trước điều đầu tiên. Filter so khớp chương La Mã nêu trong câu hỏi. Khi nạp lại cùng các ID, số điểm của A là 224 → 224, B là 180 → 180. C dùng collection của B. Chạy test ở tiến trình riêng đọc lại store đã lưu. Chạy dev mới xây lại collection để loại bỏ chunk cũ nếu đầu vào thay đổi.

Đã tái lập từ bản sao sạch của cây bài làm local với venv mới, cài phụ thuộc và tải lại PDF cùng model theo README. Đổi mã và benchmark sang CRLF giữa dev và test để kiểm tra hash. Cả 63 lượt truy vấn và 189 kết quả khớp thứ hạng, ID chunk, điểm cosine và nhãn so khớp nguyên văn. [Biên bản tái lập](../../results/reproduction_check.json)

## Cấu hình và benchmark

- **A** chia cửa sổ 500 ký tự, overlap 50, giới hạn trong từng trang.
- **B** nhóm theo chương, điều và đoạn trong từng trang, tối đa 800 ký tự. Đoạn quá dài tách ở khoảng trắng.
- **C** dùng nguyên index của B và bật filter `chapter` nếu câu hỏi cung cấp chương. So sánh B–C thay đúng một yếu tố. A–B so sánh cả cách cắt và tham số độ dài, nên hiệu ứng quan sát là của hai cấu hình chunking đầy đủ.

21 câu được xác minh theo trang và điều trong PDF. Có 15 dev từ Chương I–IV, 6 test từ Chương VI–VIII và 3 câu lọc ở mỗi tập. Tách theo chương giúp giảm câu trùng điều khoản, nhưng hai tập dùng chung một văn bản và nhiều thuật ngữ. Tiêu chí chốt trước là ưu tiên Hit@3 dev, rồi Hit@1, rồi số chunk thấp hơn, cuối cùng theo thứ tự A, B, C. Lựa chọn B được ghi lúc 10:16:11, trước khi test bắt đầu lúc 10:16:30. [Benchmark và cách tái tạo gold](../../benchmark/README.md) · [Log chạy](../../results/pipeline.log)

Lịch sử công cụ cục bộ ghi nhận lưu benchmark, split, gold và quy tắc chọn cấu hình hoàn tất lúc **10:15:15**, trước khi gọi lệnh dev lúc **10:15:32** và trước log bắt đầu dev lúc **10:15:35** ngày 14/11/2026, giờ Việt Nam. Tái dựng 21 câu và gold từ các lệnh đã ghi cho SHA-256 trùng với benchmark hiện tại và bản ghi dev gốc. Biên bản đối chiếu được lập sau thí nghiệm từ các sự kiện có sẵn, với thời gian theo đồng hồ máy. [Biên bản đối chiếu lịch sử](../../artifacts/original_benchmark_provenance.json)

## Kết quả

Bảng dưới là số đo tự động theo đoạn gold đã chốt. Thời gian ingest gồm embedding tài liệu và ghi collection, đo một lần sau khi tải model vào bộ nhớ. C dùng chung thời gian xây index của B và phát sinh 0 giây xây index riêng.

| Chiến lược | Tập | Hit@1 | Evidence Hit@3 | Chunk | Ingest (s) | Phí API |
|---|---|---:|---:|---:|---:|---:|
| A | dev | 7/15 | 9/15 | 224 | 13,41 | 0 USD |
| B | dev | 10/15 | 13/15 | 180 | 11,85 | 0 USD |
| C | dev | 10/15 | 13/15 | 180 | dùng chung B | 0 USD |
| A | test | 4/6 | 4/6 | 224 | dùng index dev | 0 USD |
| B | test | 5/6 | 5/6 | 180 | dùng index dev | 0 USD |
| C | test | 5/6 | 6/6 | 180 | dùng chung B | 0 USD |

Codex rà cả **189 kết quả** trên trace đã lưu theo cùng tiêu chí cho A/B/C. Một chunk được tính hit nếu khớp gold hoặc tự chứa đủ nội dung trả lời và có nguồn, trang truy vết được. Mỗi dòng lưu ID câu, ID chunk, hạng, trang, offsets, quyết định và lý do. Có 50 kết quả khớp nguyên văn, 4 kết quả tương đương và 135 kết quả chưa đủ bằng chứng. Bốn trường hợp tương đương là A/Q02, A/Q06, A/Q11 và A/Q14 trên dev. [Bảng rà soát](../../results/evidence_review.csv) · [Số đo sau rà soát](../../results/metrics_evidence_review.json)

| Chiến lược | Hit@1 dev | Evidence Hit@3 dev | Hit@1 test | Evidence Hit@3 test |
|---|---:|---:|---:|---:|
| A | 10/15 | 13/15 | 4/6 | 4/6 |
| B | 10/15 | 13/15 | 5/6 | 5/6 |
| C | 10/15 | 13/15 | 5/6 | 6/6 |

Sau rà soát, A và B ngang nhau về cả hai chỉ số dev. Theo thứ tự ưu tiên đã ghi, B vẫn được chọn vì có 180 chunk so với 224 của A và đứng trước C khi hai cấu hình dùng cùng index. Bảng tự động phía trên tái lập phép so khớp nguyên văn. Lượt rà sử dụng cùng câu hỏi, dữ liệu, thứ hạng và cấu hình đã lưu.

| Chiến lược | Coherence /2 (n) | Metadata đúng | Đúng phạm vi test | Grounding 0/1/2 | Grounding TB /2 |
|---|---:|---:|---:|---:|---:|
| A | 0,90 (10) | 18/18 | 1/3 | 1 / 1 / 4 | 1,50 |
| B | 1,60 (10) | 18/18 | 0/3 | 1 / 0 / 5 | 1,67 |
| C | 1,60 (10) | 18/18 | 3/3 | 0 / 0 / 6 | 2,00 |

Coherence dùng vị trí giữa nội dung các trang 1–10 đã chốt trước. B và C chia sẻ nhãn vì cùng chunk. Metadata được đối chiếu với PDF và offsets cho cả 6 câu test × 3 kết quả mỗi cấu hình. Phạm vi đạt khi cả ba kết quả thuộc chương được nêu trong câu. Ở dev, tỷ lệ này là A 2/3, B 1/3 và C 3/3. Grounding chấm khả năng trả lời từ top-3 theo thang 0–2 và kiểm tra trang dẫn. [Coherence](../../results/audit_coherence.csv) · [Metadata](../../results/audit_metadata.csv) · [Grounding](../../results/audit_grounding.csv)

### Xác nhận rà soát thủ công

Vũ Xuân Hiếu xác nhận ngày **14/11/2026** đã mở các bảng CSV và đọc các chunk tương ứng trong phiếu đối chiếu và trace. Phạm vi gồm **20 chunk coherence** tại 10 vị trí chung (10 của A, 10 của B, C dùng lại các chunk của B) và **18 lượt grounding** (top-3 của 6 câu test trên từng cấu hình A, B và C). Sau khi rà đủ hai nhóm, học viên xác nhận giữ nguyên toàn bộ điểm và lý do hiện tại trong hai bảng.

Codex hỗ trợ triển khai mã, soạn benchmark và đề xuất điểm cùng lý do ban đầu. Vũ Xuân Hiếu trực tiếp đối chiếu các mẫu và chịu trách nhiệm về quyết định chấm cuối cùng. Các ca đã được thảo luận và chốt gồm:

- **Coherence A, trang 1 — 0 → 1.** Dù hai đầu bị cắt, đoạn giữa vẫn cho phép hiểu một phần phạm vi áp dụng của quy chế.
- **Coherence A, trang 6 — giữ 0.** Học viên xem xét đề xuất nâng điểm và quyết định giữ 0. Chunk mất chủ thể đào tạo vừa làm vừa học ở Điều 7 và kết thúc giữa đầu mục Điều 8, khiến phạm vi áp dụng thiếu rõ ràng.
- **Grounding A, Q20 — 1 → 0.** Top-3 thiếu cả hai ngưỡng xét tốt nghiệp được hỏi. Các ngưỡng ở hạng 1 thuộc phần xếp loại tốt nghiệp.

Đây là lượt tự rà soát của học viên sau khi có nhãn đề xuất, nên người rà có thể chịu ảnh hưởng từ nhãn ban đầu. Các quyết định trên áp dụng rubric theo nội dung thực tế của chunk và câu hỏi. [Nhãn coherence](../../results/audit_coherence.csv) · [Nhãn grounding](../../results/audit_grounding.csv)

## Phân tích và kết luận

- **A–B.** B tăng coherence từ 0,90 lên 1,60, giảm 44 chunk và giảm 8.728 ký tự được embedding. Ở trang 6, cửa sổ của A làm mất chủ thể đào tạo vừa làm vừa học ở Điều 7 rồi kết thúc giữa đầu mục Điều 8. Mẫu này được chấm 0 vì phạm vi áp dụng thiếu rõ ràng và phần Điều 8 không thành ý. Độ dài min/trung vị/max của A là 61/500/500 ký tự, B là 26/583,5/800. Q18 ở Điều 37 trang 38 cho thấy A tìm đến đúng trang ở hạng 2 nhưng cắt mất giới hạn 50%. B giữ cả giới hạn và điều kiện áp dụng ở hạng 1. Ngược lại ở Q12, Điều 28 trang 28, A tìm đúng ở hạng 2 còn B xếp các đoạn nói về cách dùng điểm, học chương trình thứ hai và hạng tốt nghiệp lên trước. Đoạn dài hơn có thể giữ ngữ cảnh, nhưng thứ hạng cũng phụ thuộc các ý được gộp vào vector.
- **B–C.** Q20, Điều 46 trang 48, hỏi ngưỡng để xét tốt nghiệp. A chỉ tìm được phần mở đầu Điều 46 ở hạng 3. Top-3 thiếu cả hai ngưỡng được hỏi nên grounding của A là 0. B xếp đoạn về hạng tốt nghiệp ở Điều 47 và hai đoạn Chương VII lên trước. C loại hai kết quả ngoài Chương VIII và đưa Điều 46 lên hạng 2. Điều 47 vẫn đứng hạng 1, cho thấy lọc đúng chương chưa giải quyết được nhầm lẫn giữa hai điều cùng chương. Với ba câu test không nêu chương, C trả cùng top-3 như B. Metadata nguồn và trang giúp người kiểm tra mở đúng vị trí, còn `chapter` chỉ giúp khi có phạm vi đáng tin.
- **Lựa chọn.** Giữ B theo quyết định trên dev. Báo kết quả C như quan sát về truy xuất có phạm vi. Trung vị thời gian tìm trong store trên 6 câu test là A 0,87 ms, B 0,64 ms, C 1,11 ms. Các số này loại thời gian tạo embedding query, và số lần đo còn ít nên chưa dùng để kết luận về hiệu năng triển khai.
- **Giới hạn.** Tập test chỉ có 6 câu từ một quy chế. Các chunk bị chặn ở ranh giới trang, một số đoạn qua trang có thể mất ngữ cảnh. Phép so khớp đoạn nguyên văn nhạy với độ dài gold. Nếu mở rộng, thu thập thêm câu hỏi độc lập, đánh dấu bằng chứng tương đương trước khi chạy, đo thời gian nhiều lượt và thử đoạn nhiều trang với metadata truy vết từng trang.

[Trace dev](../../results/trace_dev.json) · [Trace test](../../results/trace_test.json) · [Thống kê ingest](../../results/ingest.json) · [Tái lập trace toàn văn](../../README.md)
