import random
import math

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
    def __init__(self, gender):
        self.gender = gender

    def give_answer(self, question):
        world_list = question.split()
        weight_list = golden_prob(len(world_list))
        if self.gender == "Ж":
            weight_list = list(reversed(weight_list))
        res = random.choices(world_list, weight_list)[0]
        return res

class Examiner:
    def __init__(self, gender):
        self.gender = gender

    def give_correct_answer(self, question):
        world_list = question.split()
        available_world_list = world_list.copy()
        res = []
        while available_world_list:
            weight_list = golden_prob(len(available_world_list))
            if self.gender == "Ж":
                weight_list = list(reversed(weight_list))
            world = random.choices(world_list, weight_list)[0]
            res.append(world)
            available_world_list.remove(world)
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

class Question:
    def __init__(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            self.questions = [line.strip() for line in f if line.strip()]

    def get_random_question(self):
        return random.choice(self.questions)
