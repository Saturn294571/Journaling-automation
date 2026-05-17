# Presentation Script Draft

## 1. Introduction / Why Our Model?

### Introduction

Good afternoon everyone.
We are Team 3, and today we will present our project called "Journalizing Automation based on OCR and sLLM."
First, let me briefly introduce today's topic.

Our project focuses on how AI technology can support accounting work, especially the journalizing process.
We developed a system that can automatically analyze receipt or invoice images and generate draft journal entries using OCR and AI technologies.
The purpose of this project is not to replace accountants, but to support them by reducing repetitive accounting work and improving efficiency.

### Background

Nowadays, companies process a huge number of invoices and receipts every day.
However, journalizing is still often done manually.
Because of this, several problems occur.

First, manual journalizing takes too much time because accountants must repeatedly check transaction details and enter debit and credit information manually.

Second, human errors frequently occur during repetitive work.
For example, accountants may enter incorrect amounts or wrong account titles.

Third, repetitive accounting tasks reduce overall work efficiency.
Instead of focusing on financial analysis or decision-making, accountants often spend too much time on simple data entry tasks.

As a result, many companies are becoming more interested in accounting automation systems.

### Why OCR and sLLM?

That is why our team chose OCR and sLLM for this project.

OCR, which stands for Optical Character Recognition, is a technology that reads text from images.
For example, OCR can extract dates, seller names, amounts, and payment information from receipts or invoices.
However, OCR only reads text.
It cannot understand the accounting meaning of the transaction.

So we added an sLLM, which means a small Large Language Model.
The sLLM reads the OCR text, analyzes the transaction context, and generates a draft journal entry automatically.

In simple words:
OCR reads the text
sLLM understands the transaction

We believed that combining these two technologies could effectively support accounting automation and reduce repetitive accounting work.

---

## 2. Development

Target time: about 7 minutes

### 2-1. Opening

In this part, I will explain how our project is built and how it works.

The goal of our project is simple. When a user uploads a receipt or invoice image, the system reads the transaction information from the image and creates a basic journal entry draft.

The important point is that this system is not a complete product that replaces accountants. It is a demo showing how AI can help reduce repetitive data entry work in accounting.

---

### 2-2. Overall Structure

Our project can be divided into three main parts: frontend, backend, and deployment.

The frontend is the screen that users directly interact with. In this project, we used HTML, CSS, and JavaScript. On this screen, users can upload a receipt image and check both the OCR text and the journal entry result created by the AI model.

The backend is where the main processing happens. We used Python and FastAPI for this part. When a user uploads an image, the backend receives it, runs OCR, sends the extracted text to the AI model, validates the AI result, and saves the final output.

The deployment part means running the project on a cloud server, not only on my local computer. Our demo is currently deployed on a Google Cloud VM, and Nginx handles external browser access.

For OCR, we used Tesseract. For the AI model, we used an Ollama-based local sLLM. For saving results, we used SQLite. So the overall technology stack is HTML, CSS, JavaScript, Python FastAPI, Tesseract OCR, Ollama sLLM, SQLite, and Google Cloud VM.

---

### 2-3. Data Flow

Now I will explain how data moves through the system.

First, the user uploads a receipt or invoice image.

Second, the system uses OCR to convert the text inside the image into machine-readable text.

Third, the extracted text is sent to the sLLM, which means a small Large Language Model.

Fourth, the AI model reads the OCR text and infers what kind of accounting transaction it is. Then it creates a journal entry draft in JSON format.

Fifth, the backend does not simply trust the AI result. It checks whether debit and credit amounts are equal and whether the model used only allowed account names.

Finally, the validated result is saved in a SQLite database and displayed on the screen.

In short, the flow is: image upload, OCR, AI accounting inference, validation, saving, and display.

---

### 2-4. Why We Used OCR and sLLM

We used both OCR and an sLLM because they have different roles.

OCR is responsible for reading text from an image. For example, it can extract information such as the date, seller name, item description, amount, and payment method from a receipt.

However, OCR only reads text. It does not understand the accounting meaning of the transaction.

That is why we use an sLLM in the next step.

The sLLM reads the OCR text and tries to infer the accounting meaning. For example, it can decide whether the transaction should be treated as an expense, an account payable, or a credit card payable. Then it creates a draft journal entry using debit and credit lines.

The advantage of this structure is that each part has a clear role. OCR reads the text, the AI model interprets the meaning, and the backend checks whether the result follows basic accounting rules.

---

### 2-5. Demo and Validation

Now I will show the actual demo.

For the demo, I will use an English invoice image. The reason is that OCR usually recognizes English printed text more reliably than Korean receipt text.

This example is a repair invoice. The invoice includes parts, labor, sales tax, the total amount, and the sentence "Payment is due within 15 days."

That sentence is important. It means the transaction has not been paid immediately by cash or card. Instead, the company has an obligation to pay later. So, from an accounting perspective, we record an expense and also recognize Accounts Payable.

First, I open the deployed demo page in the browser.

Next, I upload the invoice image.

After the upload, the system runs OCR. At this stage, the text inside the image is converted into plain text.

Once the OCR result is ready, the system sends that text to the AI model and asks it to create a journal entry.

After a short wait, the result appears on the screen.

In this example, the expected result is as follows.

On the debit side, the system uses Office Supplies Expense. In our demo policy, if the document is about repair, maintenance, small equipment parts, or service invoices, and there is no more specific account available, we treat it as Office Supplies Expense.

On the credit side, the system uses Accounts Payable. This is because the invoice says payment is due within 15 days, so we treat it as an unpaid liability.

The total amount is 154.06 dollars.

So the final journal entry is Office Supplies Expense debit 154.06, and Accounts Payable credit 154.06.

The important point is that the AI is not only copying text. It reads the context of the invoice and infers what accounting treatment is needed.

However, using AI output directly can be risky.

So our backend validates the result once more.

For example, if the total debit amount and total credit amount do not match, the result is rejected.

Also, if the AI uses an account name that is not in our allowed account list, the system treats it as an error.

We added this validation because AI can generate plausible answers, but it cannot always guarantee accounting accuracy.

So the role of this system is not to replace final accounting judgment. Its role is to quickly create a journal entry draft that a human can review.

To summarize, our project consists of frontend, backend, and cloud deployment.

The user uploads an image, OCR extracts text, the sLLM interprets the accounting meaning, and the backend validates and saves the result.

This structure can reduce repetitive accounting input work, especially when a company processes many receipts and invoices.

---

## 3. Accounting Concepts In Our Project

Target time: about 3 minutes

### 3-1. Why Accounting Concepts Matter

Now I will briefly explain the accounting concepts connected to our project.

Our project is not just a technical AI demo. It is also an example of applying concepts from our Principles of Accounting class to an automation workflow.

The key concepts are accounting transaction, realization of transaction, and journaling.

---

### 3-2. Accounting Transaction

The first concept is accounting transaction.

In accounting, not every event is an accounting transaction. To be recorded as an accounting transaction, an event must affect assets, liabilities, equity, revenue, or expenses, and the effect must be measurable in money.

For example, simply looking at a product or receiving a price estimate may not be an accounting transaction yet.

However, if an invoice has been issued, the company has received a service, and the amount to be paid is clearly stated, then it can be treated as an accounting transaction.

We can apply this idea to our repair invoice demo. The service and parts were provided, the total amount of 154.06 dollars was stated, and there was a condition that payment should be made later. Therefore, it can be treated as an accounting transaction.

---

### 3-3. Realization of Transaction

The second concept is realization of transaction.

In accounting, we do not always recognize revenue or expenses just because an order exists. We need to check whether goods or services were actually provided, and whether a payment obligation has occurred.

Our AI system was designed to consider this point.

For example, if the document is only a purchase order or a quotation, the system should not treat it as a completed accounting transaction too quickly.

On the other hand, if the document is a receipt or invoice with a clear date, amount, and transaction details, it is more likely to be recognized as an accounting transaction.

This is an important standard because it prevents the AI from making accounting judgments too aggressively.

---

### 3-4. Journaling

The third concept is journaling.

Journaling is the process of recording an accounting transaction using debits and credits.

The main output of our project is exactly this: a draft journal entry.

For example, in the repair invoice, the company received repair services and parts, so an expense increased. An increase in expense is recorded on the debit side.

Also, because the company has not paid yet, it now has an obligation to pay later. This is an increase in liability, so it is recorded as Accounts Payable on the credit side.

As a result, the journal entry becomes Office Supplies Expense debit 154.06 and Accounts Payable credit 154.06.

So even though our project uses OCR and AI, its final goal is connected to the basic accounting process: identifying a transaction and recording it through journaling.

---

## 4. Future Usage / Usefulness

Now, I will explain the future usage and usefulness of our project.

One of the biggest advantages of this system is reducing repetitive accounting work.
In many companies, accountants spend a large amount of time processing invoices, receipts, and journal entries every day.
Although these tasks are important, they are also repetitive and time-consuming.

Our system can automatically generate draft journal entries from receipt or invoice images, so it can reduce manual data entry work and improve overall efficiency.
For example, instead of manually checking hundreds of invoices one by one, accountants can quickly review AI-generated drafts and focus on verification.
This can save a significant amount of time, especially for companies that process many transactions every day.

Another important point is that junior accountants can focus more on difficult or meaningful tasks.
Normally, junior accountants spend a lot of time on repetitive basic journalizing work.
However, if AI handles simple repetitive tasks, they can spend more time learning financial analysis, problem solving, and decision-making processes.
In other words, AI can support accountants rather than replace them.

In addition, our project can also be useful outside large companies.
For example, many small businesses cannot afford to hire professional accountants or purchase expensive accounting systems.
For those businesses, an AI-assisted accounting tool could become a low-cost and accessible solution.
Business owners could upload receipts and automatically organize simple accounting records without advanced accounting knowledge.

Our system may also help individuals who want to manage personal financial statements or expenses.
Some people want to manage their finances more systematically but do not want to pay for expensive private banking or financial consulting services.
In that case, AI-based accounting support tools could become a practical alternative.

As AI technology continues to develop, we believe these kinds of systems may become more common in daily business and financial management.

---

## 5. Limitations and Future Work

However, our project still has several limitations.

First, the system still requires professional accountants to review and correct the results.
Although AI can generate reasonable journal entries, it is not always perfectly accurate.
Sometimes the AI model may misunderstand the transaction context or choose incorrect account titles.
Because accounting directly affects financial records and business decisions, human validation is still very important.

Second, our system heavily depends on image quality.
If the uploaded image is blurry, tilted, dark, or contains very small text, OCR performance may decrease significantly.
As a result, incorrect OCR text can lead to incorrect accounting results.

Third, AI mistakes may become very risky in important transactions or large amounts of money.
For example, if the AI incorrectly classifies a major financial transaction, it could cause accounting errors or financial losses for the company.
Therefore, our current system should be considered an assistant tool rather than a fully autonomous accounting system.

Despite these limitations, we believe this project still has strong future potential.

In future work, we plan to expand the system beyond journalizing automation.
For example, we want to add more accounting features, human resources management functions, and product management functions.
Our long-term goal is to develop a small AI-based ERP system.
ERP stands for Enterprise Resource Planning, which is a system that integrates multiple business management functions into one platform.
If we combine accounting automation with HR and inventory management, small businesses may be able to manage their operations more efficiently using a single AI-supported system.

In the future, we also hope to improve OCR accuracy, strengthen AI validation systems, and support multilingual invoice processing.
Through these improvements, we believe AI-based accounting systems can become more practical, reliable, and useful in real business environments.
