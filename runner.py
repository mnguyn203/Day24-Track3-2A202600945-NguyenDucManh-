import sys
import traceback
import setup_answers

try:
    setup_answers.main()
except Exception as e:
    with open("crash.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
