Product Requirements Document (PRD)
NairaLens AI
Version: 1.0 (MVP)
 Status: Draft

1. Executive Summary
Product Overview
NairaLens AI is an AI-powered Financial Intelligence Platform that transforms financial data into meaningful insights. Rather than simply displaying transactions or generating charts, NairaLens learns from a user's financial behavior over time to provide personalized explanations, recommendations, and coaching.
The platform combines bank statement analysis, conversational AI, and a persistent Financial Intelligence Graph (FIG) to build an evolving understanding of each user's financial life.
Its goal is not to help users track money, but to help them understand money.

2. Problem Statement
Millions of people receive bank statements every month, yet very few truly understand what those statements reveal about their financial habits.
Traditional finance apps focus on recording transactions, budgeting, or expense tracking. While useful, they often leave users asking deeper questions:
Why am I always broke before payday?
Where does my salary actually go?
What spending habits are preventing me from saving?
Which subscriptions or expenses are unnecessary?
Am I improving financially over time?
Most existing tools present data. Very few transform that data into understandable financial intelligence.
NairaLens AI addresses this gap by acting as an intelligent financial companion that continuously learns about the user and explains their financial story in plain language.

3. Vision Statement
To become Africa's most trusted AI Financial Intelligence Platform, helping individuals make smarter financial decisions through personalized financial intelligence.

4. Mission Statement
To transform financial data into clear, personalized, and actionable financial intelligence that empowers users to make better financial decisions.

5. Target Audience
Primary Users
Young professionals
Salaried employees
Freelancers
Entrepreneurs
Individuals managing multiple bank accounts
These users typically receive regular income but struggle to understand spending patterns, savings opportunities, and long-term financial behavior.

Secondary Users (Future)
Small business owners
Families
Financial coaches
SMEs

6. Core Value Proposition
Unlike traditional budgeting or expense-tracking applications, NairaLens AI focuses on understanding rather than recording.
The platform continuously learns from financial data and user interactions to deliver personalized insights, contextual recommendations, and intelligent financial conversations.

7. Success Metrics
An MVP is considered successful if it can:
Functional Metrics
Successfully parse uploaded bank statements.
Extract transactions with high accuracy.
Categorize transactions with confidence.
Generate meaningful financial insights.
Answer user questions about uploaded financial data.
User Metrics
Users upload multiple statements over time.
Users return to ask follow-up questions.
Users report improved understanding of their finances.
Users trust the AI's explanations and recommendations.


Section 2: Product Goals
Primary Goal
Build an AI-powered financial companion that helps users understand their financial behavior by analyzing bank statements, learning from interactions, and providing personalized insights and recommendations.

Business Goals
Goal 1: Build Trust
Users should feel confident uploading sensitive financial data because the platform is transparent, secure, and explains how conclusions are reached.

Goal 2: Deliver Real Value
Every uploaded statement should produce useful insights—not just charts or categorized transactions.
The user should finish every session with a clearer understanding of their finances.

Goal 3: Learn Continuously
The system should become smarter with every upload and conversation by improving its understanding of the user's financial habits and relationships.

Goal 4: Lay a Scalable Foundation
The MVP should be designed so that future features like Open Banking, investment analysis, and financial planning can be added without major architectural changes.

3. MVP Features
Rather than a long list of features, let's prioritize what makes the MVP genuinely valuable.
Epic 1 – User Management
Features
User registration
Login
Secure authentication
Profile management
Outcome: Users have a secure personal workspace.

Epic 2 – Statement Upload & Processing
Features
Upload PDF bank statements
Validate supported formats
Extract transactions
Store statement history
Detect duplicate uploads
Outcome: The platform converts statements into structured financial data.

Epic 3 – Financial Intelligence
Features
Automatic transaction categorization
Spending analysis
Income detection
Recurring payment detection
Financial trend analysis
Outcome: Users understand what happened in their finances.

Epic 4 – AI Financial Companion
Features
AI chat interface
Ask questions about finances
Explain spending patterns
Answer questions using uploaded data
Examples:
"Where did my salary go?"
"What did I spend most on this month?"
"Compare June and July."
"What subscriptions am I paying for?"
Outcome: Users can interact naturally with their financial data.

Epic 5 – Continuous Financial Learning
Features
Ask clarification questions
Learn recurring merchants
Learn income sources
Remember confirmed relationships
Improve future analyses
Outcome: The AI becomes more personalized over time.

Epic 6 – Personalized Recommendations
Features
Spending improvement suggestions
Savings opportunities
Subscription alerts
Financial habit recommendations
Outcome: Users receive actionable advice instead of just observations.

MVP Feature Prioritization
To keep development focused, let's classify features using the MoSCoW prioritization framework.
Must Have (Launch Blockers)
These are essential for the MVP:
User authentication
PDF upload
Statement parsing
Transaction extraction
AI categorization
Financial insights
AI chat
Financial memory
Personalized recommendations
Statement history
Without these, it isn't really NairaLens.

Should Have
These add significant value but can follow shortly after launch if needed:
Confidence scoring visible to users
Multi-bank account linking (manual)
Export of insights (PDF)
Notification system (e.g., new insights ready)

Could Have
Nice-to-have features that can wait for later versions:
Goal tracking
Savings simulations
Spending forecasts
Budget creation
Financial health score
Dark mode customization
Multi-language support

Won't Have (Version 1)
These are intentionally deferred:
Direct Open Banking integration
Investment portfolio analysis
Credit score monitoring
Loan management
Family/shared accounts
Mobile applications (Android/iOS)
Voice assistant
This list is important because it protects the team from scope creep.

4. User Personas

Persona 1 — The Young Professional (Primary)
Profile
Name: Sarah
Age: 27
Occupation: Software Developer
Monthly Income: ₦450,000
Accounts:
GTBank
Opay

Pain Points
Sarah receives her salary every month.
Yet by the third week she's asking:
"Where did all my money go?"
She checks her banking app frequently.
She sees transactions.
But she doesn't understand her financial behavior.

Goals
Understand spending habits
Save more money
Identify wasteful spending
Get personalized advice
Build healthier financial habits

How NairaLens Helps
Sarah uploads her statement.
Instead of seeing 500 transactions...
She receives:
"42% of your discretionary spending this month was on food delivery."
"Weekend dining accounted for most of your increase."
"Reducing one food delivery each weekend could save approximately ₦28,000 monthly."
That's value.

Persona 2 — The Freelancer
Profile
Name: David
Age: 31
Occupation: Product Designer
Income:
Variable.
Different clients.
Different payment dates.

Pain Points
He doesn't know:
Which clients pay the most.
Which months are strongest.
Average monthly income.
Business vs personal expenses.

Goals
Understand cashflow.
Track income sources.
Separate business spending.
Improve profitability.

How NairaLens Helps
The AI learns:
Client payments
Income trends
Recurring software subscriptions
Tax-related expenses
Eventually it says:
"Client A generated 48% of your income this quarter."
or
"Adobe subscriptions increased 25% after adding two additional licenses."

Persona 3 — The Entrepreneur
Profile
Name: Amina
Runs a small business.
Uses:
Personal account.
Business account.
Wallets.
Transfers between them.

Pain Points
Her finances feel mixed together.
She doesn't know:
Business profit.
Personal spending.
Owner withdrawals.
Cashflow.

Goals
Understand the business.
Understand herself.
Separate both.

How NairaLens Helps
The AI gradually learns:
Business suppliers.
Employees.
Customers.
Salary.
Personal expenses.
Business expenses.
Without requiring complicated accounting software.

Common Needs Across All Personas
Regardless of who the user is, everyone wants to:
✅ Know where their money goes.
✅ Understand why they spend the way they do.
✅ Discover opportunities to improve.
✅ Receive recommendations they can trust.

5. User Journey
This is one of the most important parts of the PRD because it defines the experience we want users to have.

Stage 1 — Discovery
User hears about NairaLens.
Landing page promise:
Understand your money. Not just your transactions.

Stage 2 — Sign Up
Create account.
Verify email.
Login.
Nothing complicated.
Time:
Less than two minutes.

Stage 3 — Welcome
Instead of immediately asking for a statement...
We explain:
"What NairaLens does"
"What happens to your data"
"How your privacy is protected"
Then:
Upload your first statement.
Trust comes before data collection.

Stage 4 — Upload Statement
User uploads PDF.
System displays progress.
Example:
✔ Reading statement...
✔ Extracting transactions...
✔ Understanding your spending...
✔ Preparing insights...
This makes the wait feel meaningful.

Stage 5 — AI Analysis
The platform identifies:
Income
Expenses
Merchants
Categories
Recurring payments
Confidence level
Before showing results.

Stage 6 — Continuous Financial Learning
If needed:
The AI asks:
Is "ABC Technologies" your employer?
Is "David" a family member?
Is this recurring payment a subscription?
Each answer improves future analyses.

Stage 7 — Financial Story
Instead of a dashboard full of charts, the user first sees a narrative.
For example:
"You earned ₦450,000 this month. Housing and transportation remained stable, but your dining expenses increased by 18%, primarily due to weekend outings. You also maintained a healthy savings rate compared to last month."
The story provides context before diving into details.

Stage 8 — Explore Insights
Users can then navigate to:
Spending breakdown
Income analysis
Recurring payments
Merchant insights
Monthly comparisons
Recommendations
The story acts as the summary, while the detailed views support deeper exploration.

Stage 9 — Ask Questions
The user can ask:
"Where did my salary go?"
"Compare June with July."
"Why did my spending increase?"
"How much did I spend on transport this year?"
The AI responds using both transaction data and the Financial Intelligence Graph.

Stage 10 — Return
The next month:
The user uploads another statement.
The AI remembers.
The conversation becomes richer.
Fewer questions.
Better recommendations.
Greater personalization.
This is where NairaLens evolves from a tool into a companion.

6. Functional Requirements
This section defines what the system must do. These are the capabilities that the engineering team must implement.

FR-001 User Authentication
The system shall allow users to:
Register using email and password
Log in securely
Reset forgotten passwords
Log out
Manage their profile
Acceptance Criteria
Authentication uses secure password hashing.
Only authenticated users can access financial data.
User sessions are securely managed.

FR-002 Statement Upload
The system shall allow authenticated users to upload bank statement PDFs.
The system shall:
Validate supported formats
Reject invalid files
Store uploaded statements securely
Prevent duplicate uploads where possible
Acceptance Criteria
PDF upload succeeds for supported banks.
Invalid files return meaningful error messages.
Upload history is available to users.

FR-003 Transaction Extraction
After upload, the system shall:
Parse the statement
Extract transactions
Normalize data into a standard format
Store extracted transactions
Each transaction should include:
Date
Description
Debit/Credit
Amount
Balance (if available)
Source statement

FR-004 Financial Analysis
The platform shall analyze extracted transactions to identify:
Income
Expenses
Spending categories
Recurring payments
Spending trends
Monthly summaries
Merchant activity
The analysis should support future comparisons across multiple statements.

FR-005 Financial Intelligence Graph (FIG)
The system shall maintain a persistent Financial Intelligence Graph for every user.
The FIG shall:
Store confirmed relationships
Learn recurring merchants
Learn income sources
Learn recurring contacts
Store financial preferences
Improve future analyses
The graph should evolve as users upload additional statements and interact with the AI.

FR-006 AI Conversation
Users shall be able to ask natural language questions about their finances.
Example questions include:
Where did my salary go?
What did I spend most on?
Compare this month with last month.
What subscriptions am I paying for?
How much did I spend on transport this year?
Responses should combine transaction data, historical context, and learned financial relationships.

FR-007 Continuous Financial Learning
When confidence is low, the AI shall request clarification.
Examples:
Is "ABC Ltd" your employer?
Is this transfer a loan repayment?
Is this merchant a supermarket?
Confirmed answers should be stored for future use.

FR-008 Financial Insights
The system shall generate personalized insights such as:
Spending summaries
Income analysis
Savings opportunities
Recurring expense summaries
Financial behavior observations
Insights should be understandable by non-financial users.

FR-009 Personalized Recommendations
The platform shall recommend actions such as:
Reduce recurring expenses
Cancel unused subscriptions
Improve saving habits
Identify unusual spending
Monitor spending trends
Recommendations must include clear reasoning.

FR-010 Statement History
Users shall be able to:
View uploaded statements
Revisit previous analyses
Compare historical periods
Continue previous conversations

7. Non-Functional Requirements
This section defines how well the system should perform.

Performance
The system should:
Process typical bank statements in under 30 seconds.
Return AI chat responses in under 5 seconds where possible.
Support concurrent users without noticeable degradation.

Security
The system shall:
Encrypt sensitive data at rest.
Encrypt all communication using HTTPS.
Hash passwords securely (Argon2 recommended).
Implement JWT-based authentication.
Restrict users to their own financial data.
Maintain audit logs for sensitive operations.

Reliability
The platform should:
Recover gracefully from failures.
Prevent data corruption.
Ensure uploaded statements remain available.
Retry recoverable background jobs automatically.

Scalability
The architecture should support:
Additional banks.
New financial data sources.
Open Banking integration.
Increased user traffic.
Future extraction of modules into microservices.

Usability
The application should:
Be easy for non-technical users.
Explain financial concepts in plain language.
Minimize unnecessary user input.
Guide users through uncertainty rather than exposing technical errors.

Maintainability
The codebase should:
Follow modular architecture.
Be well documented.
Be easily testable.
Support future feature additions with minimal refactoring.

8. AI Behaviour & Product Principles
This section captures how the AI should behave, regardless of which language model powers it.

Principle 1: Understand Before Advising
The AI must seek sufficient context before making recommendations.
If confidence is low, it should ask clarifying questions rather than guess.

Principle 2: Explain Every Insight
Every significant insight should answer:
What happened?
Why did it happen?
Why does it matter?
What can the user do next?

Principle 3: Remember Confirmed Knowledge
Once a user confirms information (such as an employer or recurring merchant), the AI should remember it and avoid asking the same question again unless there is conflicting evidence.

Principle 4: Be Transparent
The AI should clearly communicate uncertainty.
For example:
"I'm not completely certain this payment is a subscription. Can you confirm?"

Principle 5: Respect Privacy
The AI must only use the user's financial data to provide value to that user.
It must never expose or mix information across accounts or users.

9. Release Plan & MVP Success Criteria
MVP Release Goals
Before launch, the product should be capable of:
Secure user registration and login.
Uploading and processing bank statement PDFs.
Extracting and storing transactions.
Generating financial insights.
Supporting AI conversations based on uploaded data.
Learning from user feedback over time.
Providing personalized recommendations.

Success Criteria
The MVP will be considered successful if:
Product Success
Users successfully upload and analyze statements.
AI responses are accurate, helpful, and understandable.
Users return to upload additional statements.
Technical Success
Stable backend architecture.
Secure handling of financial data.
Reliable AI workflows.
Modular foundation for future growth.
User Success
By the end of a session, the user should feel:
"I understand my finances better than I did before."

