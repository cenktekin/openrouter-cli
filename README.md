# OpenRouter CLI

**Türkçe | [English](#english)**

OpenRouter API ile etkileşim için komut satırı arayüzü.

Bu araç, kullanıcı dostu bir CLI üzerinden sohbet, dosya analizi ve MCP özellikleri sunar.

![Main Application](images/app.png)

## Özellikler

### Temel Özellikler
- **Etkileşimli Sohbet**: OpenRouter üzerinden çeşitli AI modelleriyle sohbet
- **Model Seçimi**: Geniş bir yelpazede model seçeneği
- **Anahtar Döndürme**: Birden fazla API anahtarı desteği ve otomatik döndürme
- **Şema Yönetimi**: Yanıt formatlarını tanımlama ve doğrulama
- **Yanıt Biçimlendirme**: Çoklu çıktı formatları (JSON, pretty, compact)

### Dosya Analizi
- **Görsel Analiz**: AI vision modelleriyle görüntü analizi
- **PDF İşleme**: PDF belgelerini çıkarma ve özetleme
- **Metin Analizi**: Metin dosyalarını işleme ve analiz etme
- **Kod İnceleme**: Kod dosyalarını analiz etme ve inceleme

### Gelişmiş Özellikler
- **Toplu İşleme**: Birden fazla dosyayı eşzamanlı işleme
- **Önbellek Sistemi**: Analiz sonuçlarını otomatik önbelleğe alma
- **Özel İstemler**: Özel analiz istemleri desteği
- **İlerleme Takibi**: Gerçek zamanlı ilerleme izleme

### Dosya İşlemleri
- **Desteklenen Formatlar**:
  - Görseller (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`)
  - PDF'ler (`.pdf`)
  - Metin Dosyaları (`.txt`, `.md`)
  - Kod Dosyaları (`.py`, `.js`, `.java`, `.cpp`, vb.)
- **Dosya Yönetimi**:
  - Boyut sınırları ve doğrulama
  - Uzantı filtreleme
  - Yol güvenliği kontrolleri
  - Önbellek yönetimi

## Kurulum

1. Repoyu klonlayın:
```bash
git clone https://github.com/cenktekin/openrouter-cli.git
cd openrouter-cli
```

2. Sanal ortam oluşturun ve bağımlılıkları kurun:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. OpenRouter API anahtarınızı ayarlayın:
```bash
# .env dosyası oluşturun
cp .env.example .env
# .env dosyasını düzenleyin ve API anahtarınızı ekleyin

# OPENROUTER_API_KEY=your_api_key_here
```

## Kullanım

### Etkileşimli Sohbet

```bash
# Uygulamayı başlatın
./run.sh
# veya
source venv/bin/activate && python run.py

# Komutlar:
/exit          - Sohbeti sonlandır
/clear         - Sohbet geçmişini temizle
/model         - AI modelini değiştir
/copy          - Son yanıtı kopyala
/copy all      - Tüm sohbeti kopyala
/update        - Ücretsiz modelleri OpenRouter'dan güncelle
/help          - Yardım göster
```

### Dosya Analizi

```python
from openrouter_cli.tools.file_operations.ai_ops import AIPoweredFileOperations

analyzer = AIPoweredFileOperations(
    base_dir=".",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    allowed_extensions=[".txt", ".pdf", ".jpg"],
    max_file_size=10 * 1024 * 1024
)

# Tek dosya analizi
result = await analyzer.analyze_file("image.jpg", "Bu görselde ne görüyorsun?")

# Toplu analiz
results = await analyzer.batch_analyze_files(["doc1.pdf", "doc2.pdf"], "Bu belgeleri karşılaştır")
```

### Komut Satırı Arayüzü

```bash
# Dosya analizi
python -m openrouter_cli.tools.file_operations.cli analyze image.jpg

# Toplu işleme
python -m openrouter_cli.tools.file_operations.cli batch "*.pdf"

# Önbelleği temizle
python -m openrouter_cli.tools.file_operations.cli clear-cache
```

## Docker Desteği

Docker ile çalıştırma:

```bash
docker-compose up -d
docker-compose logs -f
```

## Yapılandırma

`config.yaml` dosyası oluşturun:

```yaml
api:
  key: ${OPENROUTER_API_KEY}
  url: "https://openrouter.ai/api/v1/chat/completions"
  timeout: 30

files:
  base_dir: "."
  cache_dir: ".ai_cache"
  max_size: 10
```

## Güvenlik Özellikleri

- Yol travers koruması
- Dosya türü kısıtlamaları
- Dosya boyutu sınırları
- Güvenli API anahtarı yönetimi

## Katkıda Bulunma

1. Repoyu forklayın
2. Feature branch oluşturun (`git checkout -b feature/ozellik`)
3. Değişikliklerinizi commit edin
4. Branch'i push edin (`git push origin feature/ozellik`)
5. Pull Request açın

## Lisans

MIT License - LICENSE dosyasına bakınız.

## Teşekkürler

Bu proje [mexyusef/openrouter-cli](https://github.com/mexyusef/openrouter-cli) reposundan fork edilmiştir. Orijinal repo'ya teşekkürler!

---

<a name="english"></a>

# OpenRouter CLI (English)

A command-line interface for interacting with OpenRouter's AI models.

This tool provides a rich set of features for chat, file analysis, and MCP through a user-friendly CLI.

## Features

### Core Features
- **Interactive Chat**: Chat with various AI models through OpenRouter
- **Model Selection**: Choose from a wide range of available models
- **Key Rotation**: Support for multiple API keys with automatic rotation
- **Schema Management**: Define and validate response formats
- **Response Formatting**: Multiple output formats (JSON, pretty, compact)

### File Analysis
- **Image Analysis**: Analyze images with AI vision models
- **PDF Processing**: Extract and summarize PDF documents
- **Text Analysis**: Process and analyze text files
- **Code Review**: Analyze and review code files

### Advanced Features
- **Batch Processing**: Process multiple files concurrently
- **Caching System**: Automatic caching of analysis results
- **Custom Prompts**: Support for custom analysis prompts
- **Progress Tracking**: Real-time progress monitoring

### Supported Formats
- Images (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`)
- PDFs (`.pdf`)
- Text Files (`.txt`, `.md`)
- Code Files (`.py`, `.js`, `.java`, `.cpp`, etc.)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cenktekin/openrouter-cli.git
cd openrouter-cli
```

2. Create virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. Set up your OpenRouter API key:
```bash
# Create .env file
cp .env.example .env
# Edit .env and add your API key

# OPENROUTER_API_KEY=your_api_key_here
```

## Usage

### Interactive Chat

```bash
# Start the application
./run.sh
# or
source venv/bin/activate && python run.py

# Commands:
/exit          - Quit the chat
/clear         - Clear chat history
/model         - Switch AI model
/copy          - Copy last response
/copy all      - Copy entire conversation
/update        - Update free models from OpenRouter
/help          - Show help
```

### File Analysis

```python
from openrouter_cli.tools.file_operations.ai_ops import AIPoweredFileOperations

analyzer = AIPoweredFileOperations(
    base_dir=".",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    allowed_extensions=[".txt", ".pdf", ".jpg"],
    max_file_size=10 * 1024 * 1024
)

# Single file analysis
result = await analyzer.analyze_file("image.jpg", "Describe what you see in this image")

# Batch analysis
results = await analyzer.batch_analyze_files(["doc1.pdf", "doc2.pdf"], "Compare these documents")
```

### Command Line Interface

```bash
# Analyze a file
python -m openrouter_cli.tools.file_operations.cli analyze image.jpg

# Batch process
python -m openrouter_cli.tools.file_operations.cli batch "*.pdf"

# Clear cache
python -m openrouter_cli.tools.file_operations.cli clear-cache
```

## Docker Support

Run using Docker:

```bash
docker-compose up -d
docker-compose logs -f
```

## Configuration

Create a `config.yaml` file:

```yaml
api:
  key: ${OPENROUTER_API_KEY}
  url: "https://openrouter.ai/api/v1/chat/completions"
  timeout: 30

files:
  base_dir: "."
  cache_dir: ".ai_cache"
  max_size: 10
```

## Security Features

- Path traversal protection
- File type restrictions
- File size limits
- Secure API key handling

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/name`)
3. Commit your changes
4. Push to the branch (`git push origin feature/name`)
5. Open a Pull Request

## License

MIT License - see LICENSE file.

## Acknowledgments

This project is forked from [mexyusef/openrouter-cli](https://github.com/mexyusef/openrouter-cli). Thanks to the original repo!

## Dependencies

- openai: For OpenRouter API integration
- rich: For enhanced console output
- pyyaml: For configuration management
- cryptography: For secure operations
- tqdm: For progress tracking
- pyperclip: For clipboard operations
- python-dotenv: For environment variable management

## Requirements

- Python 3.7+
- OpenRouter API key(s)
- Operating system with file system support
