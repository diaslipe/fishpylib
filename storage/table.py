import array

class Table:
    """
    Motor de dados colunar nativo e genérico de alta performance.
    Focado em processamento out-of-core de grandes volumes de dados (CRUD).
    """
    
    # Otimização em nível de classe para remover o overhead do __dict__ da própria tabela
    __slots__ = ('schema', 'columns', 'string_pools', '_length')

    def __init__(self, schema: dict):
        """
        Inicializa a tabela configurando as estruturas nativas baseadas no schema.
        
        Tipos suportados no schema:
        - 'int': Inteiro de 8 bytes (array 'q')
        - 'int_short': Inteiro de 2 bytes (array 'H')
        - 'int_byte': Inteiro de 1 byte (array 'B')
        - 'float': Double-precision de 8 bytes (array 'd')
        - 'data_inteira': Datas convertidas para AAAAMMDD de 4 bytes (array 'I')
        - 'texto_mascarado_byte': IDs de texto externos de 1 byte (array 'B')
        - 'texto_mascarado_short': IDs de texto externos de 2 bytes (array 'H')
        - 'texto_livre_altamente_repetitivo': Strings internas mascaradas automaticamente (array 'I')
        - 'texto_unico' ou 'texto_unico_nullable': Strings de baixa repetição (list com sys.intern)
        """
        self.schema = schema
        self.columns = {}
        self.string_pools = {}
        self._length = 0
        
        # Alocação dinâmica e otimizada das colunas com base nas instruções do usuário
        for col_name, col_type in schema.items():
            
            # 1. Alocação de Inteiros (Contíguos em C-level)
            if col_type == "int":
                self.columns[col_name] = array.array('q')
            elif col_type == "int_short" or col_type == "texto_mascarado_short":
                self.columns[col_name] = array.array('H')
            elif col_type == "int_byte" or col_type == "texto_mascarado_byte":
                self.columns[col_name] = array.array('B')
                
            # 2. Alocação de Pontos Flutuantes
            elif col_type == "float":
                self.columns[col_name] = array.array('d')
                
            # 3. Alocação de Datas Otimizadas
            elif col_type == "data_inteira":
                self.columns[col_name] = array.array('I')
                
            # 4. Alocação de Strings Repetitivas (Mascaramento Automático)
            elif col_type == "texto_livre_altamente_repetitivo":
                self.columns[col_name] = array.array('I')  # Guarda apenas os IDs gerados
                # Cria a estrutura de dicionário reverso para busca em O(1)
                self.string_pools[col_name] = {
                    "to_id": {},      # Tradução rápida durante escrita (String -> ID)
                    "to_string": []   # Tradução rápida durante leitura (ID -> String)
                }
                
            # 5. Alocação de Strings Únicas e Dados com Nulls
            elif col_type in ("texto_unico", "texto_unico_nullable"):
                self.columns[col_name] = []  # Fallback controlado para listas do Python
                
                # Se for anulável, cria um bitmask paralelo de validação a C-level
                if col_type == "texto_unico_nullable":
                    mask_name = f"_mask_{col_name}"
                    self.columns[mask_name] = array.array('B')

