# sps-budget-analysis
Budget Analysis and data extraction from Seattle Public Schools Budget Documentation

See [elementary_school_data_extract.ipynb](elementary_school_data_extract.ipynb) for details and draft analysis including K-Means clustering by enrollment, budget, and distance to nearest school.

Streamlit app deployed publicly for analysis [here:](https://sps-budget-analysis-2023.streamlit.app/)

## FAQ:
Q1: Where did this data come from?

A1: All of the data originated from PDFs available through the SPS public website. A number of scripts were developed in order to scrape this data accurately into a format which is usable, filterable, and one can interact with.

Some additional data was created using standard methods fully disclosed within the Jupyter Lab notebook referenced above. These include: 
* `Necessary Budget` which uses linear regression to calculate the predicted budget for each school using past years budget and enrollment numbers, 
* `Distance to nearest School` which identifies the nearest school (E, K-8 or K-12) 'as the crow flies', 
* `Budget Efficiency` which simply divides the total budget by the number of enrolled students, 
* `Disadvantage Score` which is the sum of Bilingual Education Enrolled Students, Free and Reduced Lunch Students and Special Education Students divided by the total number of enrolled students, and
* `Building area per Student (sf)` which is the building area divided by the total number of enrolled students.
* `Cluster_x` was done using k-nearest neighbor across some initial data. I didn't see much value in continuing to develop clusters, as most of the value I saw was in observing the impacts made by closing a school. 
***
Q2: How did you re-allocate student counts when simulating a closure of a school?

A2: This was tricky, without specific information on individual students' census block & current assigned school. By using the tables from the Attendance Area Report for each school, students were simply re-distributed to schools they were in attendace areas for but who went instead to a school simulated for closure. For students who were within the school's attendance area, and attended the school simulated for closure, they were re-allocated weighted proportionally to the percentage of students who traveled from the school's attendance area to other schools. 
***
Q3: Did you account for multiple closures which may have otherwise re-distributed students to another closed school? 

A3: Yes. That was a fun problem to solve. It's all in the code, within the reallocate_student_counts() functions. Long story short, it's an interative problem to solve, and lends very well to code in order to implement. Some matrix math is utilized to make this easier, and ensure that students aren't lost if there are dependencies between schools which are closed. If you simulate more than 35 schools closing, the tool tends to do some weird things, which would be addressed by adding additional capabilities to this function.
***
Q4: What about naming differenes of the schools between documents? How'd you handle that? 

A4: A big chunk of the pre-work for this exercise was the data cleanup. All of the schools alternative names were mapped back to a single consistent name, which you'll see presented in any of the datasets. 
***
Q5: Can I download the data myself? 

A5: Yes. Top-right of any of the tables in the web app, you can click the download button. Also, you can see what data I used or consolidated in my code. 
***
Q6: I have a feature I want to build into it. Can I? 

A6: Yes. Issue a pull request, or talk to me about what you'd like to see, and I'll try to work it in. 
***
Q7: I see an error. Where can I notify someone about it? 

A7: All of this is provided with no warranty, and was done on my own time voluntarily, so take that into account. I've gone through a fairly rigorous quality assurance process to make sure that the data and analyses that people may do with this app are accurate. That said, just let me know if there's a problem. I'll investigate. 
***