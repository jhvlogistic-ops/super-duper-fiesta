# llm_fallback

Cliente Python minimalista con **fallback automatico** entre los mejores modelos
de IA accesibles via API gratuita para escribir codigo:

1. **Claude Sonnet 4.5** via [GitHub Models](https://github.com/marketplace/models) (gratis con rate-limits diarios).
2. **Gemini 2.5 Pro** via [Google AI Studio](https://aistudio.google.com/apikey) (1M de contexto, tier gratuito generoso).
3. **DeepSeek V3.1** via [DeepSeek API](https://platform.deepseek.com) (no es gratis pero cuesta centimos por millon de tokens).

Si Claude se queda sin cuota diaria, el cliente cambia automaticamente a
Gemini, y si Gemini falla, a DeepSeek. Todo con una sola API.

Funciona en **Windows, macOS y Linux**, con dependencias minimas (`httpx`).

---

## Instalacion

### Opcion A: instalar como paquete (recomendado para QuantLabX / Atlas Lab)

```bash
pip install git+https://github.com/jhvlogistic-ops/super-duper-fiesta.git
```

Para soportar archivos `.env` automaticamente:

```bash
pip install "llm-fallback[dotenv] @ git+https://github.com/jhvlogistic-ops/super-duper-fiesta.git"
```

### Opcion B: copiar la carpeta `src/llm_fallback/` directamente

Si prefieres no anadir una dependencia, copia `src/llm_fallback/` dentro de
tu proyecto. Solo necesita `httpx` (`pip install httpx`).

---

## Configuracion de credenciales

Necesitas **al menos una** de las tres variables de entorno siguientes. Si
configuras varias, el cliente las usara como cadena de fallback.

| Variable | Modelo | Donde obtenerla |
|---|---|---|
| `GITHUB_MODELS_TOKEN` | Claude Sonnet 4.5 | https://github.com/settings/personal-access-tokens (scope: `models:read`) |
| `GOOGLE_API_KEY` | Gemini 2.5 Pro | https://aistudio.google.com/apikey |
| `DEEPSEEK_API_KEY` | DeepSeek V3.1 | https://platform.deepseek.com |

### En Windows (PowerShell)

```powershell
# Solo para la sesion actual:
$env:GITHUB_MODELS_TOKEN = "ghp_xxxxxxxxxxxx"
$env:GOOGLE_API_KEY      = "AIzaxxxxxxxxxxxx"

# Para todas las sesiones futuras del usuario:
setx GITHUB_MODELS_TOKEN "ghp_xxxxxxxxxxxx"
setx GOOGLE_API_KEY      "AIzaxxxxxxxxxxxx"
```

### En Linux / macOS

```bash
export GITHUB_MODELS_TOKEN="ghp_xxxxxxxxxxxx"
export GOOGLE_API_KEY="AIzaxxxxxxxxxxxx"
```

### Con archivo `.env` (cualquier OS)

Copia `.env.example` a `.env` y rellena las claves. Se carga automaticamente
si instalas la extra `dotenv` (`pip install "llm-fallback[dotenv]"`).

---

## Uso rapido

```python
from llm_fallback import LLM

llm = LLM()
print(llm.chat("Escribe una funcion Python que invierta una lista."))
```

### Streaming

```python
for chunk in llm.stream("Explica brevemente que es un decorador en Python."):
    print(chunk, end="", flush=True)
```

### Mensajes estilo OpenAI

```python
llm.chat([
    {"role": "system", "content": "Eres un experto en Python"},
    {"role": "user", "content": "Refactoriza esta funcion: ..."},
])
```

### Acceso a la respuesta completa

```python
provider, payload = llm.raw("hola")
print(provider.name)         # 'github-models-claude'
print(payload["usage"])      # tokens, etc.
```

### Override por llamada

```python
# Forzar Gemini para esta llamada concreta:
from llm_fallback import LLM, GEMINI_FLASH
llm = LLM(providers=[GEMINI_FLASH])

# O cambiar parametros:
llm.chat("...", temperature=0.2, max_tokens=2000)
```

### CLI

```bash
# Despues de `pip install ...`:
llm-fallback "Escribe quicksort en Python"

# O via `python -m`:
python -m llm_fallback "Refactoriza este snippet..."

# Listar providers disponibles segun las variables de entorno actuales:
llm-fallback --list-providers
```

---

## Personalizar la lista de proveedores

Cualquier endpoint compatible con la API de OpenAI vale (Groq, OpenRouter,
Mistral, Together, etc.):

```python
from llm_fallback import LLM, ProviderConfig
from llm_fallback.providers import CLAUDE_SONNET_45

groq = ProviderConfig(
    name="groq-qwen3-coder",
    base_url="https://api.groq.com/openai/v1",
    api_key_env="GROQ_API_KEY",
    model="qwen/qwen3-coder-30b",
)

llm = LLM(providers=[groq, CLAUDE_SONNET_45])
```

---

## Comportamiento ante errores

| Codigo | Accion |
|---|---|
| `200 OK` | Devuelve la respuesta. |
| `429` (rate limit) | Pone al proveedor en cooldown (60s por defecto) y prueba el siguiente. |
| `401` / `403` (auth) | Deshabilita el proveedor para el resto de la sesion. |
| `5xx` / timeout | Reintenta con backoff exponencial (2 intentos) y luego pasa al siguiente. |
| Todos fallan | Lanza `AllProvidersFailedError` con el detalle por proveedor. |

Los cooldowns no se persisten entre procesos: cada nueva ejecucion empieza
con los tres proveedores activos.

---

## Para QuantLabX y Atlas Lab (en Windows)

Desde la carpeta de tu proyecto:

```powershell
# Instalar
pip install git+https://github.com/jhvlogistic-ops/super-duper-fiesta.git

# Configurar al menos una clave (la mas estable: Gemini)
setx GOOGLE_API_KEY "AIzaxxxxxxxxxxxx"

# Reabrir la terminal y probar
python -c "from llm_fallback import LLM; print(LLM().chat('hola'))"
```

Si trabajas en Cursor/VS Code con la extension Continue o Cline, puedes
seguir usando esas mismas claves directamente sin este wrapper. El wrapper
es util cuando llamas al modelo **desde tu propio codigo** (por ejemplo,
desde scripts de QuantLabX que generan informes o explican datos).

---

## Desarrollo

```bash
pip install -e ".[dev]"
python -m pytest
```

---

## Licencia

MIT.
