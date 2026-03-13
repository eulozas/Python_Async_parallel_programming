import random
import math
import time
import sys
import os
from prettytable import PrettyTable
from multiprocessing import Process, Queue, Manager

PHI = (1 + math.sqrt(5)) / 2


def golden_prob(n):
    weight_list = []
    rest = 1.0
    for _ in range(n - 1):
        prob = rest / PHI
        weight_list.append(prob)
        rest -= prob

    weight_list.append(rest)
    return weight_list


# ____КЛАССЫ_____
class Student:
    def __init__(self, name, gender):
        if not name:
            raise ValueError("Некорректное имя студента")
        if gender not in {"М", "Ж"}:
            raise ValueError("Некорректный пол студента")
        self.name = name
        self.gender = gender

    def give_answer(self, question):
        world_list = question.split()
        weight_list = golden_prob(len(world_list))
        if self.gender == "Ж":
            weight_list = list(reversed(weight_list))
        res = random.choices(world_list, weight_list)[0]
        return res


class Examiner:
    exam_start_time = None

    def __init__(self, name, gender):
        if not name:
            raise ValueError("Некорректное имя экзаменатора")
        if gender not in {"М", "Ж"}:
            raise ValueError("Некорректный пол экзаменатора")
        self.name = name
        self.gender = gender
        self.lunch = 0

    def check_lunch_break(self):
        if not self.lunch and time.monotonic() - self.exam_start_time >= 30:
            self.lunch = random.uniform(12, 18)
            time.sleep(self.lunch)

    def give_correct_answer(self, question):
        world_list = question.split()
        res = []
        while world_list:
            weight_list = golden_prob(len(world_list))
            if self.gender == "Ж":
                weight_list = list(reversed(weight_list))
            world = random.choices(world_list, weight_list)[0]
            res.append(world)
            world_list.remove(world)
            if random.random() >= 1 / 3:
                break
        return res

    @staticmethod
    def get_mood():
        r = random.random()
        if r < 1 / 8:
            return "bad"
        elif r < 1 / 8 + 5 / 8:
            return "neutral"
        else:
            return "good"

    def make_decision(self, answer, correct_answer, mood):
        if mood == "bad":
            return False
        elif mood == "good":
            return True
        else:
            return answer in correct_answer

    def exam_duration(self):
        duration = random.uniform(len(self.name) - 1, len(self.name) + 1)
        return duration

    def examine_student(self, student, questions):
        q = questions.get_random_questions(3)
        mood = self.get_mood()
        results = []
        question_results = []
        for i, question in enumerate(q, 1):
            student_answer = student.give_answer(question)
            correct_answers = self.give_correct_answer(question)
            decision = self.make_decision(student_answer, correct_answers, mood)
            results.append(decision)
            question_results.append((question, decision))
        final_result = sum(results)
        return final_result >= 2, question_results


class Question:
    def __init__(self, filename):
        dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            self.questions = [line.strip() for line in f if line.strip()]
        if not self.questions:
            raise ValueError("Файл вопросов пуст или содержит только пустые строки")

    def get_random_questions(self, n):
        if n > len(self.questions):
            raise ValueError("Запрошено больше вопросов, чем есть в банке")
        return random.sample(self.questions, n)


# __________Вспомогательные функции____________
def load_participants(filename, cls):
    dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    participants_list = []
    for i, line in enumerate(lines, 1):
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"Некорректная строка в {filename}:{i}")
        participants_list.append(cls(*parts))
    if not participants_list:
        raise ValueError(f"Файл {filename} пуст или содержит только пустые строки")
    return participants_list


def check_duplicates(items, get_name, label):
    seen = set()
    duplicates = []
    for item in items:
        key = get_name(item)
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    if duplicates:
        dup_str = ", ".join(duplicates)
        raise ValueError(f"Дубли {label}: {dup_str}")


def examiner_process(
    examiner,
    queue,
    questions,
    students_state,
    examiners_state,
    question_state,
    question_state_lock,
    exam_start_time,
    error_queue,
):
    examiner.exam_start_time = exam_start_time
    try:
        while True:
            student = queue.get()
            if student is None:
                tmp_state_ex = dict(examiners_state[examiner.name])
                tmp_state_ex["finish_time"] = time.monotonic()
                examiners_state[examiner.name] = tmp_state_ex
                break

            # Статус экзаменатора в начале
            tmp_state_ex = dict(examiners_state[examiner.name])
            tmp_state_ex["current_student"] = student.name
            examiners_state[examiner.name] = tmp_state_ex

            res, question_results = examiner.examine_student(student, questions)
            duration = examiner.exam_duration()
            time.sleep(duration)

            # Статус экзаменатора в конце
            tmp_state_ex = dict(examiners_state[examiner.name])
            tmp_state_ex["total_students"] += 1
            tmp_state_ex["current_student"] = "-"
            if not res:
                tmp_state_ex["failed"] += 1
            examiners_state[examiner.name] = tmp_state_ex

            # Статус student в конце
            tmp_state_st = dict(students_state[student.name])
            tmp_state_st["finish_time"] = time.monotonic()
            if res:
                tmp_state_st["status"] = "Сдал"
            else:
                tmp_state_st["status"] = "Провалил"
            students_state[student.name] = tmp_state_st

            # Статистика по вопросам
            for question, decision in question_results:
                if decision:
                    with question_state_lock:
                        question_state[question] = question_state.get(question, 0) + 1

            examiner.check_lunch_break()
    except ValueError as e:
        error_queue.put(str(e))
        tmp_state_ex = dict(examiners_state[examiner.name])
        tmp_state_ex["current_student"] = "-"
        tmp_state_ex["finish_time"] = time.monotonic()
        examiners_state[examiner.name] = tmp_state_ex
        sys.exit(1)
    except Exception:
        tmp_state_ex = dict(examiners_state[examiner.name])
        tmp_state_ex["current_student"] = "-"
        tmp_state_ex["finish_time"] = time.monotonic()
        examiners_state[examiner.name] = tmp_state_ex
        sys.exit(1)


# _______Главный процесс экзамена________
def run_exam():
    Examiner.exam_start_time = time.monotonic()

    students = load_participants("students.txt", Student)
    examiners = load_participants("examiners.txt", Examiner)
    questions = Question("questions.txt")

    check_duplicates(students, lambda s: s.name, "студентов")
    check_duplicates(examiners, lambda e: e.name, "экзаменаторов")
    check_duplicates(questions.questions, lambda q: q, "вопросов")

    queue = Queue()
    error_queue = Queue()
    manager = Manager()
    students_state = manager.dict()
    examiners_state = manager.dict()
    question_state = manager.dict()
    question_state_lock = manager.Lock()

    for student in students:
        queue.put(student)
        students_state[student.name] = {"status": "Очередь", "finish_time": None}
    for examiner in examiners:
        queue.put(None)
        examiners_state[examiner.name] = {
            "current_student": "-",
            "total_students": 0,
            "failed": 0,
            "start_time": Examiner.exam_start_time,
            "finish_time": None,
        }
    for question in questions.questions:
        question_state[question] = 0

    processes = []

    for examiner in examiners:
        p = Process(
            target=examiner_process,
            args=(
                examiner,
                queue,
                questions,
                students_state,
                examiners_state,
                question_state,
                question_state_lock,
                Examiner.exam_start_time,
                error_queue,
            ),
        )
        p.start()
        processes.append(p)

    students_order = [s.name for s in students]
    print_status_process = Process(
        target=print_status,
        args=(
            students_state,
            examiners_state,
            question_state,
            Examiner.exam_start_time,
            len(students),
            students_order,
        ),
    )

    print_status_process.start()
    for p in processes:
        p.join()
        if p.exitcode and p.exitcode != 0:
            for other in processes:
                if other.is_alive():
                    other.terminate()
            if print_status_process.is_alive():
                print_status_process.terminate()
            for other in processes:
                other.join()
            print_status_process.join()
            if not error_queue.empty():
                raise ValueError(error_queue.get())
            raise RuntimeError(f"Процесс экзаменатора завершился с кодом {p.exitcode}")
    print_status_process.join()


# _______Функция вывода статистики(информации о ходе и результатах экзамена)________
def print_status(
    students_state,
    examiners_state,
    question_state,
    exam_start_time,
    total_students,
    students_order,
):

    while True:
        os.system("cls" if os.name == "nt" else "clear")

        table_students = PrettyTable()
        table_students.field_names = ["Студент", "Статус"]
        queue = []
        passed = []
        failed = []

        for name in students_order:
            data = students_state[name]
            if data["status"] == "Очередь":
                queue.append((name, data["status"]))
            elif data["status"] == "Сдал":
                passed.append((name, data["status"]))
            else:
                failed.append((name, data["status"]))

        for row in queue + passed + failed:
            table_students.add_row(row)

        print(table_students)

        table_examiners = PrettyTable()
        table_examiners.field_names = [
            "Экзаменатор",
            "Текущий студент",
            "Всего студентов",
            "Завалил",
            "Время работы",
        ]

        for name, data in examiners_state.items():
            if data["finish_time"] is None:
                work_time = round(time.monotonic() - data["start_time"], 2)
            else:
                work_time = round(data["finish_time"] - data["start_time"], 2)
            table_examiners.add_row(
                [
                    name,
                    data["current_student"],
                    data["total_students"],
                    data["failed"],
                    work_time,
                ]
            )

        print(table_examiners)

        # Доп. строки
        remaining = sum(1 for s in students_state.values() if s["status"] == "Очередь")

        print(f"\nОсталось в очереди: {remaining} из {total_students}")
        print(
            f"Время с начала экзамена: {round(time.monotonic() - exam_start_time, 2)}"
        )

        all_finished = all(
            data["finish_time"] is not None for data in examiners_state.values()
        )

        if all_finished and remaining == 0:
            break

        time.sleep(0.5)

    os.system("cls" if os.name == "nt" else "clear")

    # Финальный вывод

    # Таблица студенты
    table_students = PrettyTable()
    table_students.field_names = ["Студент", "Статус"]
    passed = []
    failed = []
    for name in students_order:
        data = students_state[name]
        if data["status"] == "Сдал":
            passed.append((name, data["status"]))
        else:
            failed.append((name, data["status"]))
    for row in passed + failed:
        table_students.add_row(row)
    print(table_students)

    # Таблица экзаменаторы
    table_examiners = PrettyTable()
    table_examiners.field_names = [
        "Экзаменатор",
        "Всего студентов",
        "Завалил",
        "Время работы",
    ]
    for name, data in examiners_state.items():
        work_time = round(data["finish_time"] - data["start_time"], 2)

        table_examiners.add_row(
            [name, data["total_students"], data["failed"], work_time]
        )
    print(table_examiners)

    # Время экзамена
    total_exam_time = round(time.monotonic() - exam_start_time, 2)
    print(
        f"\nВремя с момента начала экзамена и до момента его завершения: {total_exam_time}"
    )

    # Лучшие студенты
    passed_students = [
        name for name, data in students_state.items() if data["status"] == "Сдал"
    ]
    if passed_students:
        min_time = min(students_state[name]["finish_time"] for name in passed_students)
        best_students = [
            name
            for name in passed_students
            if students_state[name]["finish_time"] == min_time
        ]
        best_student_str = ", ".join(best_students)
    else:
        best_student_str = "-"
    print(f"Имена лучших студентов: {best_student_str}")

    # Лучшие экзаменаторы
    min_rate = min(
        (data["failed"] / data["total_students"] if data["total_students"] else 0)
        for data in examiners_state.values()
    )
    best_examiners = [
        name
        for name, data in examiners_state.items()
        if (data["failed"] / data["total_students"] if data["total_students"] else 0)
        == min_rate
    ]
    print(f"Имена лучших экзаменаторов: {', '.join(best_examiners)}")

    # Отчисление
    failed_students = [
        name for name, data in students_state.items() if data["status"] == "Провалил"
    ]
    if failed_students:
        expelled_student = min(
            failed_students, key=lambda name: students_state[name]["finish_time"]
        )
    else:
        expelled_student = "-"
    print(f"Имена студентов, которых после экзамена отчислят: {expelled_student}")

    # Лучшие вопросы
    if question_state:
        max_correct = max(question_state.values())
        if max_correct > 0:
            best_questions = [
                q for q, cnt in question_state.items() if cnt == max_correct
            ]
            best_question_str = ", ".join(best_questions)
        else:
            best_question_str = "-"
    else:
        best_question_str = "-"
    print(f"Лучшие вопросы: {best_question_str}")

    # Итог экзамента
    passed_count = len(passed_students)
    failed_count = len(failed_students)
    total = passed_count + failed_count
    if total > 0 and passed_count / total > 0.85:
        result = "экзамен удался"
    else:
        result = "экзамен не удался"
    print(f"Вывод: {result}")


if __name__ == "__main__":
    try:
        run_exam()
    except (ValueError, RuntimeError) as e:
        os.system("cls" if os.name == "nt" else "clear")
        print(str(e))
