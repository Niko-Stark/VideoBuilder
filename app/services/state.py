import threading

class StepProgress:
    def __init__(self, steps=0,weight = 1):
        self.steps = steps
        self.completed_steps = 0
        self.lock = threading.Lock()
        self.weight = weight

    def set_steps(self,steps):
        self.steps = steps

    def update_progress(self, steps_completed):
        with self.lock:
            self.completed_steps = min(self.steps, steps_completed)

    @property
    def progress(self):
        with self.lock:
            return self.completed_steps / self.steps if self.steps > 0 else 0


class TaskProgress:
    def __init__(self, weight = 1):
        self.sub_tasks = []
        self.lock = threading.Lock()
        self.weight = weight

    def append_sub_progress(self,sub_task):
        self.sub_tasks.append(sub_task)

    def set_sub_progress(self,sub_tasks):
        self.sub_tasks = sub_tasks
        
    @property
    def progress(self):
        with self.lock:
            total_weight = sum(task.weight for task in self.sub_tasks)
            weighted_sum = sum(task.progress * task.weight for task in self.sub_tasks)
            return weighted_sum / total_weight if total_weight > 0 else 0
