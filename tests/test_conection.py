from src.db.conection import get_vector_conn

def test_connection():
    try:
        print("🔄 Tentando conectar ao banco de dados...")
        
        conn = get_vector_conn()
        cursor = conn.cursor()
        
        # Testa a conexão
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("✅ Conexão bem-sucedida!")
        print(f"📊 Versão do PostgreSQL: {db_version['version']}")
        
        # Verifica se as tabelas existem
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('chat_ia', 'users')
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Tabelas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Conta registros
        cursor.execute("SELECT COUNT(*) as total FROM chat_ia")
        total_messages = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        print(f"\n💬 Total de mensagens: {total_messages}")
        print(f"👥 Total de usuários: {total_users}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Tudo funcionando perfeitamente!")
        
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        print("\n🔍 Verifique:")
        print("   - Se o arquivo .env está configurado corretamente")
        print("   - Se o PostgreSQL está rodando")
        print("   - Se as credenciais estão corretas")

if __name__ == "__main__":
    test_connection()