import queue
import threading
import testing
import time

num_worker_threads = 7  # 8 better than 4, 16 worse than 8, 7 optimal?
resp = queue.Queue()


def worker():
    while True:
        item = q.get()
        if item is None:
            break
        resp.put(testing.get_mod_info_list(item))
        q.task_done()

a = time.time()

q = queue.Queue()
threads = []
for i in range(num_worker_threads):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

for i in range(1, testing.get_number_pages() + 1):
    q.put(i)

# block until all tasks are done
q.join()
c = time.time()
# stop workers
for i in range(num_worker_threads):
    q.put(None)
for t in threads:
    t.join()

with open("data2", "w") as file:
    while not resp.empty():
        list_ = resp.get()
        for i in list_:
            file.write(i.__repr__() + "\n")
        resp.task_done()

print("took:", time.time() - a)