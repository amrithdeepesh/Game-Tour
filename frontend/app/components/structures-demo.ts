export type ParticipantRecord = {
  student_id: string;
  name: string;
  game: string;
};

type Node<T> = { value: T; next: Node<T> | null };

export class ParticipantLinkedList {
  private head: Node<ParticipantRecord> | null = null;
  private tail: Node<ParticipantRecord> | null = null;

  load(records: ParticipantRecord[]) {
    this.head = null;
    this.tail = null;
    for (const record of records) this.insertAtEnd(record);
  }

  insertAtEnd(value: ParticipantRecord) {
    const node: Node<ParticipantRecord> = { value, next: null };
    if (this.tail) this.tail.next = node;
    else this.head = node;
    this.tail = node;
  }

  deleteByStudentId(studentId: string) {
    let previous: Node<ParticipantRecord> | null = null;
    let current = this.head;
    while (current) {
      if (current.value.student_id === studentId) {
        if (previous) previous.next = current.next;
        else this.head = current.next;
        if (this.tail === current) this.tail = previous;
        return current.value;
      }
      previous = current;
      current = current.next;
    }
    return null;
  }

  traverse() {
    const records: ParticipantRecord[] = [];
    let current = this.head;
    while (current) {
      records.push(current.value);
      current = current.next;
    }
    return records;
  }
}

export class LinkedStack<T> {
  private top: Node<T> | null = null;

  push(value: T) {
    this.top = { value, next: this.top };
  }

  pop() {
    if (!this.top) return null;
    const value = this.top.value;
    this.top = this.top.next;
    return value;
  }

  toArray() {
    const values: T[] = [];
    let current = this.top;
    while (current) {
      values.push(current.value);
      current = current.next;
    }
    return values;
  }
}

export class LinkedQueue<T> {
  private front: Node<T> | null = null;
  private rear: Node<T> | null = null;

  enqueue(value: T) {
    const node: Node<T> = { value, next: null };
    if (this.rear) this.rear.next = node;
    else this.front = node;
    this.rear = node;
  }

  dequeue() {
    if (!this.front) return null;
    const value = this.front.value;
    this.front = this.front.next;
    if (!this.front) this.rear = null;
    return value;
  }

  toArray() {
    const values: T[] = [];
    let current = this.front;
    while (current) {
      values.push(current.value);
      current = current.next;
    }
    return values;
  }
}
