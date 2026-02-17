from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.controllers.clients_controller import ClientsController
from app.controllers.confirmations_controller import ConfirmationsController
from app.controllers.departments_controller import DepartmentsController
from app.controllers.orders_controller import OrdersController
from app.controllers.products_controller import ProductsController
from app.controllers.stores_controller import StoresController


class FastApiConfig:
    def __init__(self):
        self.app = self._create_app()
        self._configure_cors()
        ClientsController(self.app)
        ConfirmationsController(self.app)
        DepartmentsController(self.app)
        OrdersController(self.app)
        ProductsController(self.app)
        StoresController(self.app)

    def _create_app(self) -> FastAPI:
        app = FastAPI(
            title="Cross-Docking API",
            description="API for managing cross-docking orders",
            version="1.0.0",
            docs_url="/docs",
            redoc_url=None,
            openapi_url="/openapi.json",
        )

        return app

    def _configure_cors(self):
        origins = ["*"]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            max_age=600,
        )

    def get_app(self) -> FastAPI:
        return self.app
