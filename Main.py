import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from flask import Flask, render_template_string, request, redirect, session
from threading import Thread

# Configurações
ADMIN_ID = 1451570927711158313
ALLOWED_SERVERS = [1458471374812090389, 1458234841370984663]
PANEL_PASSWORD = "breno9890"

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Arquivo de dados
DATA_FILE = 'scripts_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"categorias": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Verificação de servidor
def is_allowed_server():
    async def predicate(interaction: discord.Interaction):
        if interaction.guild_id not in ALLOWED_SERVERS:
            await interaction.response.send_message("❌ Este bot não funciona neste servidor!", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

# Evento quando bot fica online
@bot.event
async def on_ready():
    print(f'✅ Bot online como {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print(f'Servidores permitidos: {len(ALLOWED_SERVERS)}')
    print('----------------------------')
    
    await bot.change_presence(
        activity=discord.Game(name="Scripts Hub 🚀"),
        status=discord.Status.online
    )
    
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

# Comando /scripts - Lista de scripts
@bot.tree.command(name="scripts", description="Ver todos os scripts disponíveis")
@is_allowed_server()
async def scripts(interaction: discord.Interaction):
    data = load_data()
    
    if not data['categorias']:
        await interaction.response.send_message("📭 Nenhuma categoria de scripts cadastrada ainda!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎮 Scripts Hub - Categorias Disponíveis",
        description="Selecione uma categoria abaixo para ver os scripts:",
        color=discord.Color.blue()
    )
    
    for idx, cat in enumerate(data['categorias'], 1):
        script_count = len(cat.get('scripts', []))
        embed.add_field(
            name=f"{idx}. {cat['nome']}",
            value=f"📜 {script_count} script(s) disponível(is)",
            inline=False
        )
    
    view = CategoryView(data['categorias'])
    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

# View para seleção de categoria
class CategoryView(discord.ui.View):
    def __init__(self, categorias):
        super().__init__(timeout=180)
        self.categorias = categorias
        
        # Adiciona botões para cada categoria (máximo 25)
        for idx, cat in enumerate(categorias[:25]):
            button = discord.ui.Button(
                label=cat['nome'],
                style=discord.ButtonStyle.primary,
                custom_id=f"cat_{idx}"
            )
            button.callback = self.create_callback(idx)
            self.add_item(button)
    
    def create_callback(self, idx):
        async def callback(interaction: discord.Interaction):
            cat = self.categorias[idx]
            
            if not cat.get('scripts'):
                await interaction.response.send_message(f"📭 A categoria **{cat['nome']}** não tem scripts ainda!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"📂 {cat['nome']}",
                description=f"Total de scripts: {len(cat['scripts'])}",
                color=discord.Color.green()
            )
            
            for script in cat['scripts']:
                code_preview = script['codigo'][:100] + "..." if len(script['codigo']) > 100 else script['codigo']
                embed.add_field(
                    name=f"📜 {script['nome']}",
                    value=f"**Autor:** {script.get('autor', 'Desconhecido')}\n```lua\n{code_preview}\n```",
                    inline=False
                )
            
            view = ScriptView(cat['scripts'])
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        return callback

# View para copiar scripts
class ScriptView(discord.ui.View):
    def __init__(self, scripts):
        super().__init__(timeout=300)
        self.scripts = scripts
        
        # Adiciona select menu para escolher script
        options = []
        for idx, script in enumerate(scripts[:25]):
            options.append(
                discord.SelectOption(
                    label=script['nome'][:100],
                    description=f"Autor: {script.get('autor', 'Desconhecido')}"[:100],
                    value=str(idx)
                )
            )
        
        select = discord.ui.Select(
            placeholder="Selecione um script para copiar",
            options=options
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        idx = int(interaction.data['values'][0])
        script = self.scripts[idx]
        
        await interaction.response.send_message(
            f"✅ **{script['nome']}** - Código:\n```lua\n{script['codigo']}\n```",
            ephemeral=True
        )

# Comando ping
@bot.tree.command(name="ping", description="Verificar latência do bot")
@is_allowed_server()
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latência: {latency}ms")

# ==================== PAINEL WEB ====================

app = Flask(__name__)
app.secret_key = os.urandom(24)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scripts Hub - Painel Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; margin-bottom: 30px; text-align: center; }
        h2 { color: #764ba2; margin: 20px 0; }
        .login-form, .categoria-form {
            max-width: 400px;
            margin: 50px auto;
        }
        input, textarea {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        button:hover { opacity: 0.9; }
        .btn-danger { background: #e74c3c; }
        .categoria {
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .script-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border: 1px solid #ddd;
        }
        .script-code {
            background: #282c34;
            color: #abb2bf;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            margin: 10px 0;
            max-height: 200px;
            overflow-y: auto;
        }
        .add-script-btn { background: #27ae60; }
        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        {% if not logged_in %}
        <div class="login-form">
            <h1>🔐 Login - Painel Admin</h1>
            <form method="POST" action="/login">
                <input type="password" name="password" placeholder="Digite a senha" required>
                <button type="submit">Entrar</button>
            </form>
        </div>
        {% else %}
        <button class="logout-btn btn-danger" onclick="location.href='/logout'">Sair</button>
        <h1>🎮 Scripts Hub - Painel de Administração</h1>
        
        <h2>➕ Adicionar Nova Categoria</h2>
        <form method="POST" action="/add_categoria">
            <input type="text" name="nome" placeholder="Nome da categoria (ex: Blox Fruits)" required>
            <button type="submit">Criar Categoria</button>
        </form>

        <h2>📂 Categorias Cadastradas</h2>
        {% for cat in categorias %}
        <div class="categoria">
            <h3>{{ cat.nome }}</h3>
            
            <h4>Scripts ({{ cat.scripts|length }}):</h4>
            {% for script in cat.scripts %}
            <div class="script-item">
                <strong>📜 {{ script.nome }}</strong><br>
                <small>👤 Autor: {{ script.autor }}</small>
                <div class="script-code">{{ script.codigo }}</div>
                <form method="POST" action="/delete_script" style="display:inline;">
                    <input type="hidden" name="cat_idx" value="{{ loop.index0 }}">
                    <input type="hidden" name="script_idx" value="{{ loop.index0 }}">
                    <button type="submit" class="btn-danger">Deletar Script</button>
                </form>
            </div>
            {% endfor %}

            <h4>➕ Adicionar Script:</h4>
            <form method="POST" action="/add_script">
                <input type="hidden" name="cat_idx" value="{{ loop.index0 }}">
                <input type="text" name="nome" placeholder="Nome do script" required>
                <input type="text" name="autor" placeholder="Autor" required>
                <textarea name="codigo" rows="5" placeholder="Código do script" required></textarea>
                <button type="submit" class="add-script-btn">Adicionar Script</button>
            </form>

            <form method="POST" action="/delete_categoria" style="margin-top:15px;">
                <input type="hidden" name="cat_idx" value="{{ loop.index0 }}">
                <button type="submit" class="btn-danger">Deletar Categoria</button>
            </form>
        </div>
        {% endfor %}
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'logged_in' not in session:
        return render_template_string(HTML_TEMPLATE, logged_in=False)
    
    data = load_data()
    return render_template_string(HTML_TEMPLATE, logged_in=True, categorias=data['categorias'])

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == PANEL_PASSWORD:
        session['logged_in'] = True
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/add_categoria', methods=['POST'])
def add_categoria():
    if 'logged_in' not in session:
        return redirect('/')
    
    data = load_data()
    nome = request.form.get('nome')
    data['categorias'].append({'nome': nome, 'scripts': []})
    save_data(data)
    return redirect('/')

@app.route('/add_script', methods=['POST'])
def add_script():
    if 'logged_in' not in session:
        return redirect('/')
    
    data = load_data()
    cat_idx = int(request.form.get('cat_idx'))
    
    script = {
        'nome': request.form.get('nome'),
        'autor': request.form.get('autor'),
        'codigo': request.form.get('codigo')
    }
    
    data['categorias'][cat_idx]['scripts'].append(script)
    save_data(data)
    return redirect('/')

@app.route('/delete_script', methods=['POST'])
def delete_script():
    if 'logged_in' not in session:
        return redirect('/')
    
    data = load_data()
    cat_idx = int(request.form.get('cat_idx'))
    script_idx = int(request.form.get('script_idx'))
    
    del data['categorias'][cat_idx]['scripts'][script_idx]
    save_data(data)
    return redirect('/')

@app.route('/delete_categoria', methods=['POST'])
def delete_categoria():
    if 'logged_in' not in session:
        return redirect('/')
    
    data = load_data()
    cat_idx = int(request.form.get('cat_idx'))
    del data['categorias'][cat_idx]
    save_data(data)
    return redirect('/')

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# Inicia o servidor web
keep_alive()

# Inicia o bot
TOKEN = os.environ.get('DISCORD_TOKEN')
bot.run(TOKEN)
