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

### Gelişmiş Özellikler
- **Otomatik Komut Tamamlama**: Tab tuşu ile komut önerileri
- **Renkli Arayüz**: Rich kütüphanesi ile görsel zenginlik
- **Komut Geçmişi**: Yukarı/aşağı ok tuşları ile geçmişteki mesajlara erişim
- **Sohbet Geçmişi Yönetimi**: /copy ve /copy all komutları ile kopyalama
- **Ayarlar Yönetimi**: /temperature ve /top_p parametreleri ile model davranışını ayarlama

### Dosya Analizi
- **Görsel Analiz**: AI vision modelleriyle görüntü analizi
- **PDF İşleme**: PDF belgelerini çıkarma ve özetleme
- **Metin Analizi**: Metin dosyalarını işleme ve analiz etme
- **Kod İnceleme**: Kod dosyalarını analiz etme ve inceleme
- **Toplu İşleme**: Birden fazla dosyayı eşzamanlı işleme
- **Önbellek Sistemi**: Analiz sonuçlarını otomatik önbelleğe alma
- **Özel İstemler**: Özel analiz istemleri desteği

### MCP Özellikleri
- **MCP Sunucu Yönetimi**: /mcp servers ile yapılandırılmış sunucuları listeleme
- **MCP Bağlantısı**: /mcp connect ile sunuculara bağlanma
- **MCP Araçları**: /mcp list ile kullanılabilir araçları görme
- **MCP Kullanımı**: /mcp use ile araçları kullanma
- **MCP Durumu**: /mcp status ile bağlantı durumunu kontrol etme

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
# .env dosyası oluşturun (.env.example varsa otomatik kopyalanır)
cp .env.example .env
# .env dosyasını düzenleyin ve API anahtarınızı ekleyin

# OPENROUTER_API_KEY=your_api_key_here

# Alternatif olarak proje dizininde OPENROUTER_API_KEYS.json oluşturun:
# [
#   "your_api_key_here"
# ]
```

## Kullanım

### Etkileşimli Sohbet

```bash
# Uygulamayı başlatın
./run.sh
# veya
source venv/bin/activate && python run.py
```

**Komutlar:**
- `/help` - Yardım göster
- `/model` - AI modelini değiştir
- `/clear` - Sohbet geçmişini temizle
- `/copy` - Son yanıtı kopyala
- `/copy all` - Tüm sohbeti kopyala
- `/analyze <file>` - Dosya analizi yap
- `/batch <pattern>` - Toplu dosya analizi
- `/clear-cache` - Önbelleği temizle
- `/update` - Ücretsiz modelleri OpenRouter'dan güncelle
- `/search <query>` - DuckDuckGo ile web araması
- `/temperature <0.0-2.0>` - Model sıcaklığını ayarla
- `/top_p <0.0-1.0>` - top_p değerini ayarla
- `/settings` - Mevcut ayarları göster
- `/mcp servers` - MCP sunucularını listele
- `/mcp connect <name>` - MCP sunucusuna bağlan
- `/mcp disconnect` - MCP bağlantısını kes
- `/mcp list` - MCP araçlarını listele
- `/mcp use <tool> --arg=value` - MCP aracını kullan
- `/mcp status` - MCP durumunu göster
- `/exit` veya `/quit` - Sohbeti sonlandır

**Özellikler:**
- **Otomatik Tamamlama**: `/` yazınca Tab tuşu ile komut önerileri gelir
- **Geçmiş**: Yukarı/aşağı ok tuşları ile geçmişteki mesajlara erişebilirsiniz
- **Renkli Çıktı**: Rich kütüphanesi ile görsel olarak zengin çıktı

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

This tool provides a rich set of features for chat, file analysis, and MCP through a user-friendly CLI with auto-completion and colorful output.

## Features

### Core Features
- **Interactive Chat**: Chat with various AI models through OpenRouter
- **Model Selection**: Choose from a wide range of available models
- **Key Rotation**: Support for multiple API keys with automatic rotation
- **Schema Management**: Define and validate response formats
- **Response Formatting**: Multiple output formats (JSON, pretty, compact)

### Advanced Features
- **Auto-Completion**: Tab-completion for commands
- **Colorful Interface**: Rich visual output with Rich library
- **Command History**: Navigate through past messages with arrow keys
- **Chat History Management**: Copy last response or entire conversation
- **Settings Management**: Adjust model behavior with /temperature and /top_p

### File Analysis
- **Image Analysis**: Analyze images with AI vision models
- **PDF Processing**: Extract and summarize PDF documents
- **Text Analysis**: Process and analyze text files
- **Code Review**: Analyze and review code files
- **Batch Processing**: Process multiple files concurrently
- **Caching System**: Automatic caching of analysis results
- **Custom Prompts**: Support for custom analysis prompts

### MCP Features
- **MCP Server Management**: List configured servers with /mcp servers
- **MCP Connection**: Connect to servers with /mcp connect
- **MCP Tools**: View available tools with /mcp list
- **MCP Usage**: Use tools with /mcp use
- **MCP Status**: Check connection status with /mcp status

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
# Create .env file (automatically copied from .env.example if available)
cp .env.example .env
# Edit .env and add your API key

# OPENROUTER_API_KEY=your_api_key_here

# Alternatively, create OPENROUTER_API_KEYS.json in project directory:
# [
#   "your_api_key_here"
# ]
```

## Usage

### Interactive Chat

```bash
# Start the application
./run.sh
# or
source venv/bin/activate && python run.py
```

**Commands:**
- `/help` - Show help
- `/model` - Switch AI model
- `/clear` - Clear chat history
- `/copy` - Copy last response
- `/copy all` - Copy entire conversation
- `/analyze <file>` - Analyze a file
- `/batch <pattern>` - Batch analyze files
- `/clear-cache` - Clear cache
- `/update` - Update free models from OpenRouter
- `/search <query>` - Web search with DuckDuckGo
- `/temperature <0.0-2.0>` - Set model temperature
- `/top_p <0.0-1.0>` - Set top_p value
- `/settings` - Show current settings
- `/mcp servers` - List MCP servers
- `/mcp connect <name>` - Connect to MCP server
- `/mcp disconnect` - Disconnect from MCP
- `/mcp list` - List MCP tools
- `/mcp use <tool> --arg=value` - Use MCP tool
- `/mcp status` - Show MCP status
- `/exit` or `/quit` - Quit chat

**Features:**
- **Auto-Completion**: Type `/` and press Tab to see command suggestions
- **History**: Use up/down arrow keys to navigate through past messages
- **Colorful Output**: Rich visual output with the Rich library

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

1. Fork repository
2. Create a feature branch (`git checkout -b feature/name`)
3. Commit your changes
4. Push to branch (`git push origin feature/name`)
5. Open a Pull Request

## License

MIT License - see LICENSE file.

## Acknowledgments

This project is forked from [mexyusef/openrouter-cli](https://github.com/mexyusef/openrouter-cli). Thanks to the original repo!

## Dependencies

- openai: For OpenRouter API integration
- rich: For enhanced console output
- prompt_toolkit: For auto-completion and rich input
- pyyaml: For configuration management
- cryptography: For secure operations
- tqdm: For progress tracking
- pyperclip: For clipboard operations
- python-dotenv: For environment variable management

## Requirements

- Python 3.7+
- OpenRouter API key(s)
- Operating system with file system support
