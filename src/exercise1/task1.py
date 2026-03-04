import random
import math
import time
import os
from multiprocessing import Process, Queue

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
        self.lunch_is_over = False

    def check_lunch_break(self):
        if not self.lunch_is_over and time.time() - self.exam_start_time >= 15: #ИЗМЕНИТЬ на 30!!!
            d = time.time()
            pause = random.uniform(12, 18)
            print(f"{self.name} идёт на обед через {d - self.exam_start_time} после начала. Обед на {pause} секунд")
            time.sleep(pause)
            self.lunch_is_over = True
            print(f"{self.name} возвращается с обеда! и время прошло {time.time() - d}")
            #СМ!!!! экзамен идет пока все ушедшие на обед с обеда не вернуться!!!!!!!!!!!!

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
            print(f"Вопрос {i}: {question}")

            student_answer = student.give_answer(question)
            correct_answers = self.give_correct_answer(question)

            print(f"Ответ: {student_answer}")
            print(f"Правильнй: {correct_answers}")

            decision = self.make_decision(student_answer, correct_answers)
            results.append(decision)

            print("Верно?", decision)

        final_result = sum(results)

        print(f"Итог {student.name}: ", final_result)

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

def examiner_process(examiner, queue, questions):
    while True:
        student = queue.get()
        if student is None:
            break
        print(f"{examiner.name} принимает {student.name}")
        examiner.examine_student(student, questions)
        duration = examiner.exam_duration()
        time.sleep(duration)
        print(f"{examiner.name} закончил принимать {student.name}")
        examiner.check_lunch_break()
        #+ОБРАБОТКА ОШИБОК!!!!!!!

def run_exam():
    Examiner.exam_start_time = time.time()
    print(Examiner.exam_start_time)
    students = load_files("students.txt", Student)
    examiners = load_files("examiners.txt", Examiner)
    questions = Question("questions.txt")
    queue = Queue()

    for student in students:
        queue.put(student)
    for _ in examiners:
        queue.put(None)

    processes = []

    for examiner in examiners:
        p = Process(target=examiner_process, args=(examiner, queue,  questions))
        p.start()
        processes.append(p)

    for p in processes: #+ОБРАБОТКА ОШИБОК!!!!!!!
        p.join()

    print("Экзамен завершён")
    print(time.time() - Examiner.exam_start_time)


if __name__ == "__main__":
    run_exam()