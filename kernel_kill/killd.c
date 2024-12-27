#include <linux/init.h> 
#include <linux/module.h> 
#include <linux/sched/signal.h>
#include <linux/sched/task.h>
#include <linux/sched/mm.h>
MODULE_LICENSE("BSD");
static int pid = -1;
module_param(pid, int, S_IRUGO);

// void print_task_state(struct task_struct *tsk) {
//     char state = task_state_char(tsk->state);
//     printk(KERN_INFO "Task state: %c\n", state);
// }

static int killd_init(void) 
{ 
    struct task_struct * p;
    printk(KERN_ALERT "killd: force D status process to death\n");
    printk(KERN_ALERT "killd: pid=%d\n", pid);
    //read_lock(&tasklist_lock);
    for_each_process(p){ 
        if(p->pid == pid){ 
            printk("killd: found\n");
            p->state = TASK_STOPPED;
            printk(KERN_ALERT "killd: aha, dead already\n");
            return 0;
        }
    }
    printk("not found\n");
    //read_unlock(&tasklist_lock);
    return 0;
} 
static void killd_exit(void) 
{ 
    printk(KERN_ALERT "killd: bye\n");
} 
module_init(killd_init);
module_exit(killd_exit);