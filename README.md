# Day 06 · Truy xuất Quy chế đào tạo đại học ĐHQGHN

Bài cá nhân của Vũ Xuân Hiếu · L3B · 2A202603860. Mục tiêu là đo ảnh hưởng của cách chia chunk và lọc theo chương lên độ chính xác truy xuất Quy chế 3626.

## Chạy lại trên Windows PowerShell

Từ thư mục gốc của repo, dùng Python 3.11, CPU hỗ trợ chạy bản ONNX lượng tử hóa đã ghim và Internet cho bước tải. Các truy vấn và tài liệu được xử lý trên máy. Vector store là Qdrant local, lưu ở `.local/qdrant`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/fetch_inputs.ps1
.\.venv\Scripts\python.exe -m starter.src.run dev
.\.venv\Scripts\python.exe -m starter.src.run test
```

Nguồn và checksum được ghi trong [manifest](data/manifest.json). Bản có lớp chữ gồm trang in 1–52, tương ứng với trang PDF 2–53 của bản scan. Hãy mở bản scan để đối chiếu số liệu, bảng và công thức nếu thấy lỗi khi trích xuất. PDF, trọng số, chỉ mục và trace có nguyên văn nằm trong `.local/`. Các file trace trong `results/` giữ ID, score, trang, offsets và nhãn để đối chiếu bằng chính nguồn được ghim.

## Thí nghiệm

- **A** dùng cửa sổ 500 ký tự và overlap 50 ký tự trong từng trang.
- **B** nhóm các đoạn liên tiếp trong cùng chương, điều và trang, tối đa 800 ký tự. Đoạn vượt giới hạn được tách tại ranh giới từ.
- **C** dùng chung index với B và áp dụng filter `chapter` khi câu hỏi nêu chương. A và B dùng nguyên câu hỏi như C, với cùng dữ liệu, embedding và tìm kiếm cosine exact.

Mô hình [multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) của intfloat chạy qua ONNX Runtime, 384 chiều, thêm `query: ` hoặc `passage: ` theo loại đầu vào. Metadata `chapter` là danh sách số La Mã từ tiêu đề chương, `article` là danh sách số điều. Cả hai được duy trì qua chỗ ngắt trang. `page` đánh số từ 1, `start` và `end` là offset trong trang sau chuẩn hóa. Một chunk A có thể đi qua ranh giới điều/chương. Qdrant so khớp phần tử trong danh sách chương.

Lệnh dev trích xuất và kiểm tra checksum, xây hai collection, nạp lại các ID ổn định và kiểm tra số điểm. Một lần xây mới thay toàn bộ hai collection của lab để loại chunk lỗi thời. Dev ghi cấu hình được chọn trước khi lệnh test đọc lại index. Xem [benchmark](benchmark/README.md), [nhật ký](artifacts/experiment_log.csv) và [quy tắc](RULES.md).

Đã tái lập từ bản sao sạch của cây bài làm local với venv mới, cài phụ thuộc và tải lại PDF cùng model theo README. Đổi mã và benchmark sang CRLF giữa dev và test để kiểm tra hash. Cả 63 lượt truy vấn và 189 kết quả khớp thứ hạng, ID chunk, điểm cosine và nhãn so khớp nguyên văn. [Biên bản tái lập](results/reproduction_check.json)

## Kiểm tra minh chứng

- `results/metrics_dev.json`, `results/metrics_test.json` ghi Hit@1 và Evidence Hit@3 theo khớp nguyên văn gold.
- `results/evidence_review.csv` ghi quyết định cho cả 189 kết quả. Chạy `python scripts/review_evidence.py` để kiểm tra các dòng khớp trace và tái tạo `results/metrics_evidence_review.json`.
- `results/dev_selection.json` ghi lựa chọn, thời điểm và hash dữ liệu, model, benchmark và pipeline của lần chạy gốc. Lệnh dev tạo bản ghi cho lần tái lập, sau đó chạy test trong cùng bản sao. Phiên bản hiện tại chuẩn hóa LF/CRLF khi băm mã và benchmark. PDF, trọng số và tokenizer vẫn dùng hash byte.
- `results/ingest.json` ghi số chunk, phân bố độ dài, thời gian và số điểm trước/sau nạp lại.
- `.local/trace_dev_full.json` và `.local/trace_test_full.json` chứa cả câu hỏi, bằng chứng gold và nội dung chunk. Các bản để chia sẻ ở `results/` có thể kiểm chứng theo offset bằng PDF nguồn và cùng quy tắc chuẩn hóa.
