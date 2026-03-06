from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.schema import CreateColumn

from app.config import settings
from app.utilities.logger import logger
import threading

class Base(DeclarativeBase):
    __abstract__ = True


EXCLUDED_TABLES = []
TEMP_TABLES = []

DROP_EXTRA_COLUMNS = True
PROTECTED_COLUMNS = set()

# Singleton class for database connection pool
class DatabaseConnectionPool:
    """
    Clase singleton para el manejo de un pool de conexiones a bases de datos.
    """
    _instance = None
    _lock = threading.Lock()
    databases = {
        'sesamo': settings.mysql_url 
    }

    def __new__(cls):
        """
        Crear una nueva instancia de la clase si no existe, o retornar la instancia existente.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnectionPool, cls).__new__(cls)
                    cls._instance._initialize_pools()
        return cls._instance

    def _initialize_pools(self):
        """
        Inicializa los pools de conexiones a las bases de datos especificadas.
        """
        self._engines = {}
        self._sessions = {}
        for key, uri in self.databases.items():
            try:
                logger.info(f"Key: {key}, URI: {uri}")
                # pool_pre_ping es crucial en MySQL para evitar el error "MySQL server has gone away"
                self._engines[key] = create_engine(
                    uri, 
                    pool_size=50, 
                    max_overflow=100, 
                    pool_pre_ping=True, 
                    pool_recycle=3600, 
                    echo=False
                )
                self._sessions[key] = sessionmaker(autocommit=False, autoflush=False, bind=self._engines[key])
            except Exception as e:
                logger.error(f"Failed to initialize database connection pool for {key}: {str(e)}")

    def dispose_all(self):
        """
        Cierra todos los motores y sesiones en el pool.
        Útil para evitar herencia de sockets al hacer fork() con Gunicorn.
        """
        with self._lock:
            if hasattr(self, '_engines'):
                for key, engine in self._engines.items():
                    try:
                        engine.dispose()
                        logger.debug(f"Disposed engine for {key}")
                    except Exception:
                        pass
                self._engines = {}
            if hasattr(self, '_sessions'):
                self._sessions = {}
            DatabaseConnectionPool._instance = None
    
    def get_session(self, database):
        """
        Obtiene una nueva sesión de SQLAlchemy.
        """
        if database not in self._sessions:
            raise ValueError(f"Database {database} not in the list of available databases")
        return self._sessions[database]()

    @classmethod
    def get_database_uri(cls, key):
        return cls.databases.get(key, None)
    
    @classmethod
    def get_databases(cls):
        return cls.databases.keys()

def get_session(database: str):
    """
    Obtiene una sesión de SQLAlchemy para la base de datos especificada.
    """
    db_pool = DatabaseConnectionPool()
    db = db_pool.get_session(database)
    try:
        yield db
    except Exception as e:
        raise RuntimeError(f"Error al obtener sesión para {database}: {str(e)}")
    finally:
        db.rollback()
        db.close()

def get_db():
    """
    Obtiene una sesión de SQLAlchemy para la base de datos por defecto.
    """
    db_pool = DatabaseConnectionPool()
    db = db_pool.get_session('sesamo')
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def initialize_database():
    """
    Inicializa la base de datos creando las tablas necesarias y ejecutando scripts SQL.
    """
    engine = None
    logger.info("Initializing Database")
    
    temp_engine = create_engine(DatabaseConnectionPool.get_database_uri('sesamo'))
    
    try:
        with temp_engine.connect() as connection:
            lock_result = connection.execute(text("SELECT GET_LOCK('db_init_lock', 10)")).scalar()
            if not lock_result:
                logger.error("Could not acquire database lock. Another instance might be initializing.")
                return

            try:
                for key in DatabaseConnectionPool.get_databases():
                    engine = create_engine(DatabaseConnectionPool.get_database_uri(key), pool_size=5, max_overflow=10)
                    
                    Base.metadata.create_all(
                        bind=engine, 
                        tables=[t for t in Base.metadata.tables.values() if t.name not in EXCLUDED_TABLES],
                        checkfirst=True,
                    )
                    _synchronize_tables(engine)
                    _seed_database(engine)
                    engine.dispose()
                    
                logger.info("Database Initialized")
            finally:
                # Liberar el bloqueo de MySQL
                connection.execute(text("SELECT RELEASE_LOCK('db_init_lock')"))
                connection.commit()
                
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise e
    finally:
        temp_engine.dispose()

    return None


def _synchronize_tables(engine):
    """
    Actualiza las tablas existentes para que coincidan con la definición de los modelos.
    """
    inspector = inspect(engine)
    metadata_tables = [
        table for table in Base.metadata.tables.values()
        if table.name not in EXCLUDED_TABLES and table.name not in TEMP_TABLES
    ]
    with engine.begin() as connection:
        for table in metadata_tables:
            try:
                inspector_columns = inspector.get_columns(table.name)
                existing_columns = {column["name"]: column for column in inspector_columns}
            except Exception as exc:
                logger.error(f"No se pudieron inspeccionar columnas para {table.name}: {exc}")
                continue

            model_columns = {column.name for column in table.columns}

            for column in table.columns:
                if column.name in existing_columns:
                    existing_col_info = existing_columns[column.name]
                    _check_and_update_column_properties(connection, table, column, existing_col_info)
                    continue
                _add_missing_column(connection, table, column)

            if DROP_EXTRA_COLUMNS:
                existing_col_names = set(existing_columns.keys())
                _drop_extra_columns(connection, table, existing_col_names - model_columns)

def _seed_database(engine):
    """
    Seeds the database with initial data if it doesn't exist.
    """
    # Import models locally to avoid circular import
    from app.models.role import Role
    from app.models.school import School
    from app.models.category import Category
    from app.models.user import User
    from app.models.questionnaire import Questionnaire
    from app.models.question import Question
    from app.models.answer_option import AnswerOption

    logger.info("Checking for seed data...")
    
    with sessionmaker(bind=engine)() as session:
        # Seed Roles
        if session.query(Role).count() == 0:
            logger.info("Seeding Roles...")
            roles = [
                Role(name="Admin"),
                Role(name="Estudiante")
            ]
            session.add_all(roles)
            session.commit()
            logger.info("Roles seeded successfully.")
        
        # Seed Schools
        if session.query(School).count() == 0:
            logger.info("Seeding Schools...")
            schools = [
                School(name="Colegio San Bartolomé"),
                School(name="Instituto Técnico Central"),
                School(name="Liceo Nacional"),
                School(name="Gimnasio Moderno")
            ]
            session.add_all(schools)
            session.commit()
            logger.info("Schools seeded successfully.")

        # Seed Categories
        if session.query(Category).count() == 0:
            logger.info("Seeding Categories...")
            categories = [
                Category(name="Matemáticas"),
                Category(name="Ciencias"),
                Category(name="Lenguaje"),
                Category(name="Historia")
            ]
            session.add_all(categories)
            session.commit()
            logger.info("Categories seeded successfully.")
        
        # Seed Users (Admin and Test User)
        if session.query(User).count() == 0:
            logger.info("Seeding Users...")
            
            # Get IDs for relationships
            admin_role = session.query(Role).filter_by(name="Admin").first()
            student_role = session.query(Role).filter_by(name="Estudiante").first()
            school = session.query(School).first()
            
            if admin_role and school:
                admin_user = User(
                    name="Admin",
                    last_name="User",
                    email="admin@sesamo.com",
                    normalized_email="ADMIN@SESAMO.COM",
                    residential_address="Calle 123",
                    type_document_identity="CC",
                    document_identity="1234567890",
                    role_id=admin_role.id,
                    school_id=school.id
                )
                admin_user.set_password("admin123")
                session.add(admin_user)
            
            if student_role and school:
                student_user = User(
                    name="Test",
                    last_name="Student",
                    email="student@sesamo.com",
                    normalized_email="STUDENT@SESAMO.COM",
                    residential_address="Carrera 456",
                    type_document_identity="TI",
                    document_identity="0987654321",
                    role_id=student_role.id,
                    school_id=school.id
                )
                student_user.set_password("student123")
                session.add(student_user)
                
            session.commit()
            logger.info("Users seeded successfully.")

        # Seed Questionnaires
        if session.query(Questionnaire).count() == 0:
            logger.info("Seeding Questionnaires...")
            math_category = session.query(Category).filter_by(name="Matemáticas").first()
            
            if math_category:
                questionnaire = Questionnaire(
                    questionnaire_number=1,
                    category_id=math_category.id
                )
                session.add(questionnaire)
                session.commit()
                logger.info("Questionnaire seeded successfully.")
                
                # Seed Questions for the Questionnaire
                logger.info("Seeding Questions...")
                question1 = Question(
                    question_text="¿Cuánto es 2 + 2?",
                    questionnaire_id=questionnaire.id
                )
                session.add(question1)
                session.commit()
                
                # Seed Answer Options
                logger.info("Seeding Answer Options...")
                options = [
                    AnswerOption(answer="3", option_key="A", is_correct=False, question_id=question1.id),
                    AnswerOption(answer="4", option_key="B", is_correct=True, question_id=question1.id),
                    AnswerOption(answer="5", option_key="C", is_correct=False, question_id=question1.id),
                    AnswerOption(answer="6", option_key="D", is_correct=False, question_id=question1.id)
                ]
                session.add_all(options)
                session.commit()
                logger.info("Questions and Answers seeded successfully.")


def _add_missing_column(connection, table, column):
    """
    Agrega una nueva columna respetando los datos existentes.
    """
    qualified_table = f"`{table.name}`"
    logger.info(f"Añadiendo columna faltante '{column.name}' a {qualified_table}")

    column_copy = column.copy()
    column_copy.nullable = True  # Primero permitir nulos para insertar en tabla con datos
    if column_copy.server_default is None and column.default is not None and column.default.is_scalar:
        column_copy.server_default = column.default.arg

    column_ddl = CreateColumn(column_copy).compile(dialect=connection.dialect)
    connection.execute(
        text(f"ALTER TABLE {qualified_table} ADD COLUMN {column_ddl}")
    )

    if column.nullable:
        return

    # En MySQL, si se requiere NOT NULL, modificamos la columna después de asegurar los datos
    if not _table_has_data(connection, qualified_table):
        new_type_sql = column.type.compile(dialect=connection.dialect)
        connection.execute(
            text(f"ALTER TABLE {qualified_table} MODIFY COLUMN `{column.name}` {new_type_sql} NOT NULL")
        )
    else:
        logger.warning(
            f"La columna '{column.name}' permanece nullable en {qualified_table} "
            "porque existen registros previos. Actualiza los datos manualmente si es necesario."
        )


def _table_has_data(connection, qualified_table):
    result = connection.execute(
        text(f"SELECT EXISTS (SELECT 1 FROM {qualified_table} LIMIT 1)")
    )
    return bool(result.scalar())


def _drop_extra_columns(connection, table, extra_columns):
    qualified_table = f"`{table.name}`"
    for column_name in extra_columns:
        if column_name in PROTECTED_COLUMNS:
            continue
        logger.warning(f"Eliminando columna sobrante '{column_name}' de {qualified_table}")
        connection.execute(
            text(f"ALTER TABLE {qualified_table} DROP COLUMN `{column_name}`")
        )


def _check_and_update_column_properties(connection, table, model_column, existing_col_info):
    """
    Compara propiedades de una columna del modelo con la de la BD (tipo, nulabilidad)
    y ejecuta los MODIFY COLUMN necesarios para MySQL.
    """
    qualified_table = f"`{table.name}`"
    
    existing_type = existing_col_info['type']
    model_type = model_column.type
    
    model_nullable = bool(model_column.nullable)
    existing_nullable = existing_col_info['nullable']

    type_changed = _types_are_different(existing_type, model_type, connection.dialect)
    nullability_changed = (model_nullable != existing_nullable)

    # MySQL requiere MODIFY COLUMN para cambiar tanto el tipo como la nulabilidad
    if type_changed or nullability_changed:
        new_type_sql = model_type.compile(dialect=connection.dialect)
        null_sql = "NULL" if model_nullable else "NOT NULL"
        
        logger.info(f"Modificando columna '{model_column.name}' en {qualified_table}: tipo={new_type_sql}, nullable={model_nullable}")
        
        try:
            connection.execute(
                text(f"ALTER TABLE {qualified_table} MODIFY COLUMN `{model_column.name}` {new_type_sql} {null_sql}")
            )
        except Exception as e:
            logger.error(f"Error al modificar la columna '{model_column.name}' de {qualified_table}: {str(e)}")


def _types_are_different(existing_type, model_type, dialect):
    """
    Compara dos tipos de SQLAlchemy renderizándolos a string SQL (Adaptado para MySQL).
    """
    try:
        existing_sql = str(existing_type.compile(dialect=dialect)).upper()
        model_sql = str(model_type.compile(dialect=dialect)).upper()
        
        # Mapeos comunes de equivalencia en MySQL
        equivalent_types = {
            'TINYINT(1)': 'BOOLEAN',
            'BOOL': 'BOOLEAN',
            'DATETIME': 'TIMESTAMP',
            'CHARACTER VARYING': 'VARCHAR',
            'INTEGER': 'INT'
        }
        
        for old, new in equivalent_types.items():
            existing_sql = existing_sql.replace(old, new)
            model_sql = model_sql.replace(old, new)

        # Ignorar longitudes si el driver omite algunas, comparando la base
        return existing_sql.split('(')[0] != model_sql.split('(')[0]
    except Exception:
        return False