from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///../aurora_saas.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    stripe_customer_id = Column(String, nullable=True)
    
    deployments = relationship("AgentDeployment", back_populates="owner")


class AgentDeployment(Base):
    __tablename__ = "agent_deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_type = Column(String)  # 'client_ecom_test', 'client_social_test', etc.
    status = Column(String, default="active")
    
    owner = relationship("User", back_populates="deployments")
    integrations = relationship("IntegrationKey", back_populates="deployment")


class IntegrationKey(Base):
    __tablename__ = "integration_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("agent_deployments.id"))
    platform = Column(String)  # e.g., 'ayrshare', 'stripe', 'shopify'
    api_key_encrypted = Column(String)  # In production, this must be securely encrypted
    
    deployment = relationship("AgentDeployment", back_populates="integrations")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
