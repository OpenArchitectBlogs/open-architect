---
layout: default
title: "Engineering Thought #28"
date: 2026-04-12
categories: [engineering]
---

# Engineering Thought #28

The strange property of memory fragmentation is that a system can report abundant free memory, yet still fail to allocate a seemingly modest chunk. Engineers often scratch their heads when `malloc` returns null or a JVM throws `OutOfMemoryError`, despite `top` showing gigabytes available. The reframe is to understand that "free memory" is a scalar value reflecting total capacity, not its topological arrangement. Fragmentation means the heap has become a Swiss cheese of small, discontiguous holes. What's needed is a large *contiguous* block, which no longer exists. The profound insight is that while capacity is monitored, contiguity is implicitly assumed. This hidden constraint forces the allocator to work harder, triggers more frequent garbage collections, and degrades cache performance, transforming an invisible structural issue into tangible latency and reliability problems, even when the overall memory budget appears healthy.