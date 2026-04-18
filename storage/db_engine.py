from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:12er34qw@localhost:4000/ocpp_test?charset=utf8mb4",
                       pool_pre_ping=True,
                       pool_recycle=1800
                       )