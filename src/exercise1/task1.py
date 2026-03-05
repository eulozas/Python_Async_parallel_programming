import random
import math
import time
import os
from prettytable import PrettyTable
from multiprocessing import Process, Queue, Manager

PHI = (1 + math.sqrt(5)) / 2

def golden_prob(n):
    weight_list = []
    rest = 1.0
    for _ in range(n-1):
        prob = rest/PHI
        weight_list.append(prob)
        rest-=prob
        
    weight_list.append(rest)
    return weight_list

class Student:
    def __init__(self, name, gender):
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
        self.name = name
        self.gender = gender
        self.lunch = 0 #может не хранить?

    def check_lunch_break(self):
        if not self.lunch and time.monotonic() - self.exam_start_time >= 15: #ИЗМЕНИТЬ на 30!!!
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
            if random.random() >= 1/3:
                break
        return res
    
    @staticmethod
    def get_mood():
        r = random.random()
        if r < 1/8:
            return "bad"
        elif r < 1/8 + 5/8:
            return "neutral"
        else:
            return "good"
        
    def make_decision(self, answer, correct_answer):
        mood = self.get_mood()
        if mood == "bad":
            return False
        elif mood == "good":
            return True
        else:
            return answer in correct_answer
        
    def exam_duration(self):
        duration = random.uniform(len(self.name)-1, len(self.name)+1)
        return duration
    
    def examine_student(self, student, questions):
        q = questions.get_random_questions(3)
        results = []
        for i, question in enumerate(q, 1):
            student_answer = student.give_answer(question)
            correct_answers = self.give_correct_answer(question)
            decision = self.make_decision(student_answer, correct_answers)
            results.append(decision)
        final_result = sum(results)
        return final_result >= 2

class Question:
    def __init__(self, filename):
        dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            self.questions = [line.strip() for line in f if line.strip()]

    def get_random_questions(self, n):
        if n > len(self.questions):
            raise ValueError("Запрошено больше вопросов, чем есть в банке")
        return random.sample(self.questions, n)


def load_files(filename, cls):
    #+ОБРАБОТКА ОШИБОК!!!!!!!
    dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = map(str.strip, f)
        return [cls(*line.split()) for line in lines if line]

def examiner_process(examiner, queue, questions, students_state, examiners_state):
    while True:
        student = queue.get()
        if student is None:
            tmp_state_ex = dict(examiners_state[examiner.name])
            tmp_state_ex["finish_time"] = time.monotonic()
            examiners_state[examiner.name] = tmp_state_ex
            break

        #Статус экзаменатора в начале
        tmp_state_ex = dict(examiners_state[examiner.name])
        tmp_state_ex["current_student"] = student.name
        examiners_state[examiner.name] = tmp_state_ex

        res = examiner.examine_student(student, questions)
        duration = examiner.exam_duration()
        time.sleep(duration)

        #Статус экзаменатора в конце
        tmp_state_ex = dict(examiners_state[examiner.name])
        tmp_state_ex["total_students"] += 1
        tmp_state_ex["current_student"] = "-"
        if not res:
            tmp_state_ex["failed"] += 1
        examiners_state[examiner.name] = tmp_state_ex
        
        #Статус student в конце
        tmp_state_st = dict(students_state[student.name])
        tmp_state_st["finish_time"] = time.monotonic()
        if res:
            tmp_state_st["status"] = "Сдал"
        else:
            tmp_state_st["status"] = "Провалил"
        students_state[student.name] = tmp_state_st

        examiner.check_lunch_break()

        #+ОБРАБОТКА ОШИБОК!!!!!!!

def run_exam():
    Examiner.exam_start_time = time.monotonic()

    students = load_files("students.txt", Student)
    examiners = load_files("examiners.txt", Examiner)
    questions = Question("questions.txt")
    queue = Queue()
    manager = Manager()
    students_state = manager.dict()
    examiners_state = manager.dict()

    for student in students:
        queue.put(student)
        students_state[student.name] = {
            "status": "Очередь",
            "finish_time": None
        }
    for examiner in examiners:
        queue.put(None)
        examiners_state[examiner.name] = {
            "current_student": "-",
            "total_students": 0,
            "failed": 0,
            #"lunch_time": 0.0,
            "start_time": Examiner.exam_start_time,
            "finish_time": None
        }

    processes = []
    for examiner in examiners:
        p = Process(target=examiner_process, args=(examiner, queue,  questions, students_state, examiners_state))
        p.start()
        processes.append(p)
    print_status_process = Process(
        target=print_status,
        args=(students_state, examiners_state,
              Examiner.exam_start_time, len(students))
    )
    print_status_process.start()
    for p in processes: #+ОБРАБОТКА ОШИБОК!!!!!!!
        p.join()
    print_status_process.join()


def print_status(students_state, examiners_state, exam_start_time, total_students):

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        table_students = PrettyTable()
        table_students.field_names = ["Студент", "Статус"]
        queue = []
        passed = []
        failed = []
    
        for name, data in students_state.items():
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
            "Время работы"
        ]

        for name, data in examiners_state.items():
            if data["finish_time"] is None:
                work_time = round(time.monotonic() - data["start_time"], 2) 
            else:
                work_time = round(data["finish_time"] - data["start_time"], 2)
            table_examiners.add_row([
                name,
                data["current_student"],
                data["total_students"],
                data["failed"],
                work_time
            ])

        print(table_examiners)

        # Доп. строки
        remaining = sum(1 for s in students_state.values()
                        if s["status"] == "Очередь")

        print(f"\nОсталось в очереди: {remaining} из {total_students}")
        print(f"Время с начала экзамена: {round(time.monotonic() - exam_start_time, 2)} сек")

        all_finished = all(data["finish_time"] is not None for data in examiners_state.values())

        if all_finished and remaining == 0:
            break

        time.sleep(0.5)

    os.system('cls' if os.name == 'nt' else 'clear')

    #Финальный вывод

    table_students = PrettyTable()
    table_students.field_names = ["Студент", "Статус"]
    passed = []
    failed = []
    for name, data in students_state.items():
        if data["status"] == "Сдал":
            passed.append((name, data["status"]))
        else:
            failed.append((name, data["status"]))
    for row in passed + failed:
        table_students.add_row(row)
    print(table_students)

    table_examiners = PrettyTable()
    table_examiners.field_names = [
        "Экзаменатор",
        "Всего студентов",
        "Завалил",
        "Время работы"
    ]
    for name, data in examiners_state.items():

        work_time = round(data["finish_time"] - data["start_time"], 2)

        table_examiners.add_row([
            name,
            data["total_students"],
            data["failed"],
            work_time
        ])
    print(table_examiners)

    total_exam_time = round(time.monotonic() - exam_start_time, 2)
    print(f"\nВремя с момента начала экзамена и до момента его завершения: {total_exam_time}")

    passed_students = [name for name, data in students_state.items() if data["status"] == "Сдал"]
    if passed_students:
        best_student = min(passed_students, key=lambda name: students_state[name]["finish_time"])
    else:
        best_student = "-"
    print(f"Имена лучших студентов: {best_student}")

    min_failed = min(data["failed"] for data in examiners_state.values())
    best_examiners = [
        name for name, data in examiners_state.items()
        if data["failed"] == min_failed
    ]
    print(f"Имена лучших экзаменаторов: {', '.join(best_examiners)}")

    failed_students = [name for name, data in students_state.items() if data["status"] == "Провалил"]
    if failed_students:
        expelled_student = min(failed_students, key=lambda name: students_state[name]["finish_time"])
    else:
        expelled_student = "-"
    print(f"Имена студентов, которых после экзамена отчислят: {expelled_student}")

    #Добавить статистику по лучшим вопросам______________________________________

    passed_count = len(passed_students)
    failed_count = len(failed_students)
    total = passed_count + failed_count
    if total > 0 and passed_count / total > 0.85:
        result = "экзамен удался"
    else:
        result = "экзамен не удался"
    print(f"Вывод: {result}")

#WINDOWS + ????
if __name__ == "__main__":
    run_exam()
