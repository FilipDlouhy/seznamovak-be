from rest_framework.routers import SimpleRouter

from .controllers.reservations import ReservationController

router = SimpleRouter(trailing_slash=False)
router.register("reservations", ReservationController, basename="reservation")

urlpatterns = router.urls
