# Benchmark Quy chế 3626

21 câu theo chủ đề, gồm 15 dev (Chương I–IV) và 6 test (Chương VI–VIII). Chia theo chương để tránh hỏi lại cùng điều khoản ở hai tập. Toàn bộ tài liệu vẫn có trong index. Sáu câu cung cấp chương làm phạm vi lọc, ba câu ở dev và ba ở test. Chương là thông tin nêu trong câu hỏi. Query đưa vào model là nguyên câu hỏi ở cả ba cấu hình.

Mỗi đoạn gold được lưu bằng nguồn, trang PDF, điều, vị trí ký tự Unicode trong trang chuẩn hóa (đầu bao gồm, cuối loại trừ) và SHA-256. Pipeline tái tạo trường evidence_quote từ PDF đã xác minh checksum, kiểm tra từng đoạn và lưu vào trace đầy đủ ở thư mục .local. Trang n của bản có lớp chữ tương ứng trang n+1 trong bản scan.

Chốt trước khi chạy. Chọn theo Evidence Hit@3 trên dev, rồi Hit@1, rồi số chunk ít hơn, cuối cùng theo thứ tự A, B, C. Giữ nguyên khi chạy test. Mẫu coherence là vị trí giữa văn bản của trang PDF 1–10. Nếu nhiều chunk phủ vị trí, chọn chunk có tâm gần vị trí nhất, sau đó ưu tiên offset đầu nhỏ hơn. C dùng chung chunk với B. Audit metadata và grounding dùng cả 6 câu test.

