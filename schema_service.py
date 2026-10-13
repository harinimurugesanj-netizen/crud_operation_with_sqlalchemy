from database import Base

def get_schema_description() -> str:
    lines = []
    for table_name, table in Base.metadata.tables.items():
        lines.append(f'Table: "{table_name}"')
        for col in table.columns:
            col_type = str(col.type)
            pk = " [primary key]" if col.primary_key else ""
            fk = ""
            if col.foreign_keys:
                targets = ", ".join(str(f.target_fullname) for f in col.foreign_keys)
                fk = f" [foreign key -> {targets}]"
            lines.append(f'  - "{col.name}": {col_type}{pk}{fk}')
        lines.append("")
    return "\n".join(lines)