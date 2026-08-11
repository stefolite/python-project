def test_endpoint():
    with TestClient(app) as client:
        response = client.get(url)
        assert response.status_code == 200



@app.middleware
async def my_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    