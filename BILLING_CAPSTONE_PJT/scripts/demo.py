import argparse
from uuid import uuid4

import httpx


DEMO_TENANT_ID = (
    "11111111-1111-1111-1111-111111111111"
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
    )

    parser.add_argument(
        "--calls",
        type=int,
        default=1001,
    )

    args = parser.parse_args()

    with httpx.Client(
        base_url=args.base_url,
        timeout=15,
    ) as client:
        for number in range(
            1,
            args.calls + 1,
        ):
            response = client.post(
                "/v1/actions/call",
                headers={
                    "X-Tenant-ID": (
                        DEMO_TENANT_ID
                    ),
                    "Idempotency-Key": (
                        f"demo-call-"
                        f"{number}-"
                        f"{uuid4()}"
                    ),
                },
            )

            if response.status_code != 200:
                print(
                    number,
                    response.status_code,
                    response.json(),
                )
                break

            if number in {
                1,
                999,
                1000,
            }:
                print(
                    number,
                    response.json(),
                )

        report = client.get(
            "/v1/usage",
            headers={
                "X-Tenant-ID": (
                    DEMO_TENANT_ID
                )
            },
        )

        print(report.json())


if __name__ == "__main__":
    main()