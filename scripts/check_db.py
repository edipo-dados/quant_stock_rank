"""
Script para verificar conexão com o banco de dados.

Uso:
    python scripts/check_db.py
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from app.models.database import engine, SessionLocal
from app.config import settings


def check_connection():
    """Verifica se é possível conectar ao banco de dados."""
    print("=" * 60)
    print("VERIFICAÇÃO DE CONEXÃO COM BANCO DE DADOS")
    print("=" * 60)
    print()
    
    print(f"📍 Database URL: {settings.database_url}")
    print()
    
    # Detecta o tipo de banco
    is_postgres = settings.database_url.startswith("postgresql://")
    is_sqlite = settings.database_url.startswith("sqlite://")
    
    if is_sqlite:
        print("⚠️  ATENÇÃO: Usando SQLite (banco em memória)")
        print("   Para usar PostgreSQL, configure DATABASE_URL no .env")
        print()
    
    try:
        # Tenta conectar
        print("🔄 Tentando conectar ao banco de dados...")
        with engine.connect() as conn:
            # Query diferente dependendo do tipo de banco
            if is_postgres:
                result = conn.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                print("✅ Conexão bem-sucedida!")
                print()
                print(f"📊 Versão do PostgreSQL:")
                print(f"   {version}")
            elif is_sqlite:
                result = conn.execute(text("SELECT sqlite_version();"))
                version = result.fetchone()[0]
                print("✅ Conexão bem-sucedida!")
                print()
                print(f"📊 Versão do SQLite:")
                print(f"   {version}")
            else:
                print("✅ Conexão bem-sucedida!")
            print()
        
        # Verifica tabelas existentes
        print("🔍 Verificando tabelas existentes...")
        with engine.connect() as conn:
            if is_postgres:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
            else:
                result = conn.execute(text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table'
                    ORDER BY name;
                """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Encontradas {len(tables)} tabelas:")
                for table in tables:
                    print(f"   - {table}")
                print()
                
                # Conta registros em cada tabela
                print("📈 Contagem de registros:")
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = result.fetchone()[0]
                    print(f"   - {table}: {count} registros")
            else:
                print("⚠️  Nenhuma tabela encontrada.")
                print("   Execute: python scripts/init_db.py")
            print()
        
        print("=" * 60)
        print("✅ VERIFICAÇÃO CONCLUÍDA COM SUCESSO")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("❌ ERRO AO CONECTAR AO BANCO DE DADOS")
        print()
        print(f"Erro: {e}")
        print()
        
        if is_postgres:
            print("💡 Possíveis soluções:")
            print("   1. Verifique se o PostgreSQL está rodando:")
            print("      docker-compose up -d postgres")
            print()
            print("   2. Verifique as credenciais no arquivo .env")
            print()
            print("   3. Verifique se a porta 5432 está disponível:")
            print("      netstat -an | findstr 5432")
            print()
        else:
            print("💡 Possível solução:")
            print("   Configure DATABASE_URL no arquivo .env para usar PostgreSQL:")
            print("   DATABASE_URL=postgresql://user:password@localhost:5432/quant_ranker")
            print()
        
        print("=" * 60)
        return False


def show_connection_info():
    """Mostra informações de conexão."""
    print()
    print("📋 INFORMAÇÕES DE CONEXÃO")
    print("-" * 60)
    print(f"Host: localhost")
    print(f"Porta: 5432")
    print(f"Database: quant_ranker")
    print(f"Usuário: user")
    print(f"Senha: password")
    print()
    print("String de conexão:")
    print("postgresql://user:password@localhost:5432/quant_ranker")
    print("-" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verifica conexão com o banco de dados"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Mostra apenas informações de conexão"
    )
    
    args = parser.parse_args()
    
    if args.info:
        show_connection_info()
    else:
        success = check_connection()
        sys.exit(0 if success else 1)
