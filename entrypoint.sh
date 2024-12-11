#!/usr/bin/env sh

main() {
    # TODO
    # python3 -m alembic upgrade head

    if [ -z "$APP" ]; then
        echo "Specify which part of the app you want to run with 'APP=...'"
        return
    fi

    unbuffer make run app=$APP
}
main $@
