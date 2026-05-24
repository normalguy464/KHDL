# 🏠 Dự Đoán Giá Bất Động Sản TP. Hồ Chí Minh

Dự án phân tích và dự đoán giá bất động sản tại TP. Hồ Chí Minh dựa trên dữ liệu thu thập từ nền tảng [moso.vn](https://moso.vn). Pipeline bao gồm toàn bộ các bước từ thu thập dữ liệu, xử lý, trực quan hóa đến huấn luyện mô hình học máy.

---

## 📁 Cấu Trúc Thư Mục

```
KHDL/
├── Crawldata/
│   └── crawl.py                          # Script thu thập dữ liệu từ moso.vn API
├── Processing/
│   └── Data_cleaning.ipynb               # Làm sạch và tiền xử lý dữ liệu
├── Visualization/
│   └── visualize.ipynb                   # Trực quan hóa phân phối giá theo quận
├── Train/
│   ├── Multi-layer_Perceptron-v3.ipynb   # Mô hình MLP (PyTorch + thủ công)
│   └── Support_Vector_Regression.ipynb  # Mô hình SVR (scikit-learn)
└── moso_filtered_20251024_164043.csv     # Dữ liệu thô đã lọc
```

---

## 🔄 Pipeline Tổng Quan

```
Thu thập dữ liệu  →  Làm sạch & Tiền xử lý  →  Trực quan hóa  →  Huấn luyện mô hình
  (crawl.py)         (Data_cleaning.ipynb)      (visualize.ipynb)   (MLP / SVR)
```

---

## 📦 Các Bước Chính

### 1. Thu Thập Dữ Liệu (`Crawldata/crawl.py`)

- Crawl dữ liệu từ API của moso.vn với bộ lọc địa lý TP. Hồ Chí Minh (GeoBox)
- Thu thập các thuộc tính: địa chỉ, giá, loại bất động sản, diện tích, số tầng, phòng ngủ, phòng tắm, nội thất, giấy tờ pháp lý
- Tự động chuẩn hóa địa chỉ bằng API `provinces.open-api.vn`
- Xử lý rate limit, retry logic và lưu kết quả ra file `.csv` và `.json`

### 2. Làm Sạch & Tiền Xử Lý (`Processing/Data_cleaning.ipynb`)

- Chuyển đổi cột giá và kích thước về kiểu số thực
- Loại bỏ outlier (giá bất thường, diện tích âm hoặc quá lớn)
- Áp dụng log-transform lên cột giá (`log_price`)
- One-hot encoding cho các biến phân loại: quận/huyện, loại BĐS, tình trạng nội thất, giấy tờ
- Giảm chiều dữ liệu kích thước (`pWidth`, `pLength`, `pArea`, `pLandArea`) bằng **PCA** xuống còn 3 thành phần chính (giải thích **94.13%** phương sai)
- Xuất file `data_for_training.csv` (41 features) để huấn luyện

### 3. Trực Quan Hóa (`Visualization/visualize.ipynb`)

- Vẽ phân phối giá bất động sản toàn thành phố
- Bản đồ choropleth TP. HCM theo giá trung bình từng quận/huyện (sử dụng GeoJSON + GeoPandas)
- Phân loại quận theo mức giá so với trung vị thành phố

### 4. Huấn Luyện Mô Hình (`Train/`)

#### Multi-layer Perceptron (`Multi-layer_Perceptron-v3.ipynb`)

Hai phiên bản MLP được triển khai và so sánh:

| Phiên bản | Framework | R² | MAE (log) | RMSE (log) |
|---|---|---|---|---|
| MLP (thư viện) | PyTorch | 0.7375 | 0.2766 | 0.3631 |
| MLP (thủ công) | NumPy | **0.7492** | **0.2716** | **0.3549** |

- Kiến trúc: `Input → 100 → 100 → 50 → 1` với activation **Tanh**
- MLP thủ công tự cài đặt forward/backward pass, Glorot initialization, SGD + Nesterov momentum, early stopping
- Chạy trên Google Colab với GPU T4

#### Support Vector Regression (`Support_Vector_Regression.ipynb`)

| Kernel | C | Epsilon | R² | MAE | RMSE |
|---|---|---|---|---|---|
| RBF | 10 | 0.1 | **0.7652** | 0.2560 | 0.3434 |

---

## 📊 Dữ Liệu

| Thuộc tính | Mô tả |
|---|---|
| `price` | Giá bất động sản (VND) |
| `pType` | Loại bất động sản (nhà phố, căn hộ, đất, ...) |
| `pWidth` / `pLength` | Chiều rộng / chiều dài (m) |
| `pArea` / `pLandArea` | Diện tích sàn / diện tích đất (m²) |
| `pNumberOfFloors` | Số tầng |
| `pNumberOfBedrooms` | Số phòng ngủ |
| `pNumberOfBathrooms` | Số phòng tắm |
| `pCertificateType` | Loại giấy tờ pháp lý |
| `pFurnitureStatus` | Tình trạng nội thất |
| `district` | Quận/huyện tại TP. HCM |

Tổng số mẫu sau làm sạch: **~2.100 bất động sản**

---

## 🛠️ Cài Đặt & Chạy

### Yêu cầu

```bash
pip install requests pandas numpy scikit-learn torch matplotlib seaborn geopandas
```

### Thu thập dữ liệu

```bash
cd Crawldata
python crawl.py
```

### Xử lý & Huấn luyện

Mở các notebook bằng Jupyter hoặc Google Colab theo thứ tự:

1. `Processing/Data_cleaning.ipynb`
2. `Visualization/visualize.ipynb`
3. `Train/Multi-layer_Perceptron-v3.ipynb` hoặc `Train/Support_Vector_Regression.ipynb`

> **Lưu ý:** Các notebook Train được tối ưu để chạy trên Google Colab (có hỗ trợ GPU).

---

## 📈 Kết Quả Tóm Tắt

| Mô hình | R² | MAE (log scale) |
|---|---|---|
| SVR (RBF) | **0.7652** | 0.2560 |
| MLP thủ công (NumPy) | 0.7492 | 0.2716 |
| MLP thư viện (PyTorch) | 0.7375 | 0.2766 |

Mô hình SVR với kernel RBF đạt hiệu suất tốt nhất trên tập test.

---

## 📚 Công Nghệ Sử Dụng

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-GPU-red?logo=pytorch)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-orange?logo=scikitlearn)
![Pandas](https://img.shields.io/badge/Pandas-2.x-blue?logo=pandas)
![GeoPandas](https://img.shields.io/badge/GeoPandas-mapping-green)
![Google Colab](https://img.shields.io/badge/Google%20Colab-GPU%20T4-yellow?logo=googlecolab)
