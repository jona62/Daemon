package com.example.daemon

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import io.grpc.ManagedChannelBuilder
import kotlinx.coroutines.runBlocking
import taskdaemon.TaskDaemonGrpcKt
import taskdaemon.empty
import taskdaemon.taskRequest
import taskdaemon.taskIdRequest
import taskdaemon.listTasksRequest

data class AddInput(val a: Int, val b: Int)

fun main() = runBlocking {
    val mapper = jacksonObjectMapper()
    
    val channel = ManagedChannelBuilder
        .forAddress("localhost", 50051)
        .usePlaintext()
        .build()

    val client = TaskDaemonGrpcKt.TaskDaemonCoroutineStub(channel)

    try {
        // Check health
        println("=== Health Check ===")
        val health = client.getHealth(empty {})
        println("Status: ${health.status}")
        println("Queue size: ${health.queueSize}")
        println("Workers: ${health.workers}")

        // Queue a task with data class
        println("\n=== Queue Task ===")
        val input = AddInput(a = 10, b = 20)
        val taskRequest = taskRequest {
            taskType = "add"
            taskDataJson = mapper.writeValueAsString(input)
        }
        val taskResponse = client.queueTask(taskRequest)
        println("Task queued with ID: ${taskResponse.taskId}")

        // Wait a bit for processing
        Thread.sleep(1000)

        // Get task details
        println("\n=== Get Task ===")
        val taskIdRequest = taskIdRequest { taskId = taskResponse.taskId }
        val task = client.getTask(taskIdRequest)
        println("Task ID: ${task.id}")
        println("Type: ${task.taskType}")
        println("Status: ${task.status}")
        println("Result: ${task.result}")

        // List tasks
        println("\n=== List Tasks ===")
        val listRequest = listTasksRequest { limit = 5 }
        val taskList = client.listTasks(listRequest)
        println("Recent tasks:")
        taskList.tasksList.forEach { t ->
            println("  - Task ${t.id}: ${t.taskType} (${t.status})")
        }

        // Get metrics
        println("\n=== Metrics ===")
        val metrics = client.getMetrics(empty {})
        println("Tasks received: ${metrics.tasksReceived}")
        println("Tasks processed (success): ${metrics.tasksProcessedSuccess}")
        println("Tasks processed (failed): ${metrics.tasksProcessedFailed}")
        println("Queue size: ${metrics.queueSize}")

    } finally {
        channel.shutdown()
    }
}
