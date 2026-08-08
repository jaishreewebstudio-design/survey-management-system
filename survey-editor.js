// =====================================================
// SURVEY EDITOR
// =====================================================

let surveyId = null;

let surveyData = {
    title: "",
    description: "",
    questions: []
};


// =====================================================
// PAGE LOAD
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    surveyId = getSurveyId();

    if (!surveyId) {
        showError("Survey ID not found.");
        return;
    }

    // Add question button
    const addQuestionButton =
        document.getElementById("addQuestionButton");

    if (addQuestionButton) {
        addQuestionButton.addEventListener(
            "click",
            addQuestion
        );
    }

    // Form submit
    const form =
        document.getElementById("surveyForm");

    if (form) {
        form.addEventListener(
            "submit",
            function (event) {

                event.preventDefault();

                saveSurvey();
            }
        );
    }

    loadSurvey();
});


// =====================================================
// GET SURVEY ID
// =====================================================

function getSurveyId() {

    // Example:
    // /surveys/5/edit
    // /edit-survey/5

    const parts =
        window.location.pathname
            .split("/")
            .filter(Boolean);

    // Search from right side for numeric ID
    for (let i = parts.length - 1; i >= 0; i--) {

        if (
            parts[i] &&
            /^\d+$/.test(parts[i])
        ) {

            return Number(parts[i]);
        }
    }


    // Try Jinja variable
    if (
        typeof window.SURVEY_ID !== "undefined" &&
        window.SURVEY_ID
    ) {

        return Number(
            window.SURVEY_ID
        );
    }


    return null;
}


// =====================================================
// LOAD SURVEY
// =====================================================

async function loadSurvey() {

    const loading =
        document.getElementById("loading");

    const form =
        document.getElementById("surveyForm");

    try {

        if (loading) {
            loading.style.display = "block";
        }

        if (form) {
            form.style.display = "none";
        }


        const response =
            await fetch(
                `/api/surveys/${surveyId}`
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Unable to load survey."
            );
        }


        surveyData =
            data.survey || {};


        surveyData.title =
            surveyData.title || "";


        surveyData.description =
            surveyData.description || "";


        surveyData.questions =
            Array.isArray(
                surveyData.questions
            )
                ? surveyData.questions
                : [];


        // Normalize questions
        surveyData.questions =
            surveyData.questions.map(
                normalizeQuestion
            );


        // IMPORTANT:
        // HTML IDs are title and description
        const titleInput =
            document.getElementById("title");

        const descriptionInput =
            document.getElementById("description");


        if (titleInput) {

            titleInput.value =
                surveyData.title;
        }


        if (descriptionInput) {

            descriptionInput.value =
                surveyData.description;
        }


        renderQuestions();


        if (loading) {
            loading.style.display = "none";
        }

        if (form) {
            form.style.display = "block";
        }


    } catch (error) {

        console.error(
            "Load survey error:",
            error
        );


        if (loading) {

            loading.innerHTML = `
                <div class="error">
                    ${escapeHtml(error.message)}
                </div>
            `;
        }


        showError(
            error.message
        );
    }
}


// =====================================================
// NORMALIZE QUESTION
// =====================================================

function normalizeQuestion(question) {

    let type =
        question.question_type ||
        question.type ||
        "short_answer";


    type =
        normalizeQuestionType(type);


    let options =
        Array.isArray(question.options)
            ? question.options
            : [];


    // Convert object options if backend sends them
    options =
        options.map(function (option) {

            if (
                typeof option === "object" &&
                option !== null
            ) {

                return (
                    option.text ||
                    option.label ||
                    option.value ||
                    ""
                );
            }

            return String(option);
        });


    // Add default options for option-based types
    if (
        isOptionType(type) &&
        options.length === 0
    ) {

        options =
            getDefaultOptions(type);
    }


    return {

        id:
            question.id || null,

        question:
            question.question ||
            question.text ||
            "",

        question_type:
            type,

        options:
            options,

        required:
            Boolean(question.required)

    };
}


// =====================================================
// NORMALIZE QUESTION TYPE
// =====================================================

function normalizeQuestionType(type) {

    if (!type) {
        return "short_answer";
    }


    const value =
        String(type)
            .trim()
            .toLowerCase()
            .replace(/[\s-]+/g, "_");


    const typeMap = {

        "short_answer":
            "short_answer",

        "shortanswer":
            "short_answer",

        "text":
            "short_answer",

        "multiple_choice":
            "multiple_choice",

        "multiplechoice":
            "multiple_choice",

        "mcq":
            "multiple_choice",

        "dropdown":
            "dropdown",

        "select":
            "dropdown",

        "checkbox":
            "checkbox",

        "checkboxes":
            "checkbox",

        "rating":
            "rating_scale",

        "rating_scale":
            "rating_scale",

        "ratingscale":
            "rating_scale",

        "likert":
            "likert_scale",

        "likert_scale":
            "likert_scale",

        "likertscale":
            "likert_scale"

    };


    return (
        typeMap[value] ||
        "short_answer"
    );
}


// =====================================================
// CHECK OPTION TYPE
// =====================================================

function isOptionType(type) {

    return [

        "multiple_choice",

        "dropdown",

        "checkbox",

        "rating_scale",

        "likert_scale"

    ].includes(
        normalizeQuestionType(type)
    );
}


// =====================================================
// DEFAULT OPTIONS
// =====================================================

function getDefaultOptions(type) {

    type =
        normalizeQuestionType(type);


    if (type === "rating_scale") {

        return [

            "1",
            "2",
            "3",
            "4",
            "5"

        ];
    }


    if (type === "likert_scale") {

        return [

            "Very Satisfied",
            "Satisfied",
            "Neutral",
            "Dissatisfied",
            "Very Dissatisfied"

        ];
    }


    return [

        "Option 1",
        "Option 2"

    ];
}


// =====================================================
// RENDER QUESTIONS
// =====================================================

function renderQuestions() {

    const container =
        document.getElementById(
            "questionsContainer"
        );


    if (!container) {

        console.error(
            "questionsContainer not found."
        );

        return;
    }


    container.innerHTML = "";


    if (
        !surveyData.questions ||
        surveyData.questions.length === 0
    ) {

        container.innerHTML = `

            <div class="empty">

                No questions added yet.

                <br><br>

                Click
                <b>+ Add Question</b>
                to create one.

            </div>

        `;

        return;
    }


    surveyData.questions.forEach(
        function (question, index) {

            const div =
                document.createElement("div");


            div.className =
                "question-card";


            div.innerHTML = `

                <div class="question-header">

                    <span class="question-number">
                        Question ${index + 1}
                    </span>

                    <button
                        type="button"
                        class="remove-btn"
                        onclick="deleteQuestion(${index})"
                    >
                        Remove
                    </button>

                </div>


                <div class="form-group">

                    <label>
                        Question
                    </label>

                    <input
                        type="text"
                        id="question-${index}"
                        placeholder="Enter your question"
                    >

                </div>


                <div class="form-group">

                    <label>
                        Question Type
                    </label>

                    <select
                        id="question-type-${index}"
                    >

                        <option value="short_answer">
                            Short Answer
                        </option>

                        <option value="multiple_choice">
                            Multiple Choice
                        </option>

                        <option value="dropdown">
                            Dropdown
                        </option>

                        <option value="checkbox">
                            Checkbox
                        </option>

                        <option value="rating_scale">
                            Rating Scale
                        </option>

                        <option value="likert_scale">
                            Likert Scale
                        </option>

                    </select>

                </div>


                <div
                    id="options-${index}"
                    class="options-box"
                ></div>


                <div class="required-row">

                    <input
                        type="checkbox"
                        id="required-${index}"
                    >

                    <label
                        for="required-${index}"
                        style="margin:0;"
                    >
                        Required question
                    </label>

                </div>

            `;


            container.appendChild(div);


            // Set question value safely
            const questionInput =
                document.getElementById(
                    `question-${index}`
                );


            if (questionInput) {

                questionInput.value =
                    question.question || "";


                questionInput.addEventListener(
                    "input",
                    function () {

                        updateQuestion(
                            index,
                            "question",
                            this.value
                        );
                    }
                );
            }


            // Set question type
            const typeSelect =
                document.getElementById(
                    `question-type-${index}`
                );


            if (typeSelect) {

                typeSelect.value =
                    normalizeQuestionType(
                        question.question_type
                    );


                typeSelect.addEventListener(
                    "change",
                    function () {

                        changeQuestionType(
                            index,
                            this.value
                        );
                    }
                );
            }


            // Required
            const requiredInput =
                document.getElementById(
                    `required-${index}`
                );


            if (requiredInput) {

                requiredInput.checked =
                    Boolean(
                        question.required
                    );


                requiredInput.addEventListener(
                    "change",
                    function () {

                        updateQuestion(
                            index,
                            "required",
                            this.checked
                        );
                    }
                );
            }


            // Render options
            renderOptions(index);

        }
    );
}


// =====================================================
// RENDER OPTIONS
// =====================================================

function renderOptions(index) {

    const question =
        surveyData.questions[index];


    const container =
        document.getElementById(
            `options-${index}`
        );


    if (!question || !container) {
        return;
    }


    const type =
        normalizeQuestionType(
            question.question_type
        );


    // No options for short answer
    if (!isOptionType(type)) {

        container.innerHTML = "";

        return;
    }


    let options =
        Array.isArray(question.options)
            ? question.options
            : [];


    // Make sure there are default options
    if (options.length === 0) {

        options =
            getDefaultOptions(type);

        question.options =
            options;
    }


    let html = `

        <div class="options-section">

            <label>
                Options
            </label>

    `;


    options.forEach(
        function (option, optionIndex) {

            html += `

                <div class="option-row">

                    <input
                        type="text"
                        class="option-input"
                        data-question="${index}"
                        data-option="${optionIndex}"
                        placeholder="Enter option"
                    >

                    <button
                        type="button"
                        class="remove-option"
                        onclick="
                            deleteOption(
                                ${index},
                                ${optionIndex}
                            )
                        "
                    >
                        Remove
                    </button>

                </div>

            `;
        }
    );


    html += `

            <button
                type="button"
                class="add-option-btn"
                onclick="
                    addOption(${index})
                "
            >
                + Add Option
            </button>

        </div>

    `;


    container.innerHTML =
        html;


    // Set input values AFTER HTML insertion
    const inputs =
        container.querySelectorAll(
            ".option-input"
        );


    inputs.forEach(
        function (input) {

            const optionIndex =
                Number(
                    input.dataset.option
                );


            input.value =
                question.options[
                    optionIndex
                ] || "";


            input.addEventListener(
                "input",
                function () {

                    updateOption(
                        index,
                        optionIndex,
                        this.value
                    );
                }
            );
        }
    );
}


// =====================================================
// ADD QUESTION
// =====================================================

function addQuestion() {

    surveyData.questions.push({

        question: "",

        question_type:
            "short_answer",

        options: [],

        required: false

    });


    renderQuestions();


    const cards =
        document.querySelectorAll(
            ".question-card"
        );


    if (cards.length > 0) {

        cards[
            cards.length - 1
        ].scrollIntoView({

            behavior: "smooth",

            block: "center"

        });
    }
}


// =====================================================
// DELETE QUESTION
// =====================================================

function deleteQuestion(index) {

    if (
        !confirm(
            "Delete this question?"
        )
    ) {

        return;
    }


    surveyData.questions.splice(
        index,
        1
    );


    renderQuestions();
}


// =====================================================
// UPDATE QUESTION
// =====================================================

function updateQuestion(
    index,
    field,
    value
) {

    if (
        !surveyData.questions[index]
    ) {

        return;
    }


    surveyData.questions[index][field] =
        value;
}


// =====================================================
// CHANGE QUESTION TYPE
// =====================================================

function changeQuestionType(
    index,
    type
) {

    const question =
        surveyData.questions[index];


    if (!question) {
        return;
    }


    type =
        normalizeQuestionType(type);


    question.question_type =
        type;


    // If selected type supports options
    if (isOptionType(type)) {

        question.options =
            getDefaultOptions(type);

    } else {

        question.options = [];
    }


    // Re-render this question
    renderQuestions();


    // Scroll back to question
    const cards =
        document.querySelectorAll(
            ".question-card"
        );


    if (cards[index]) {

        cards[index].scrollIntoView({
            behavior: "auto",
            block: "nearest"
        });
    }
}


// =====================================================
// ADD OPTION
// =====================================================

function addOption(index) {

    const question =
        surveyData.questions[index];


    if (!question) {
        return;
    }


    if (
        !Array.isArray(
            question.options
        )
    ) {

        question.options = [];
    }


    question.options.push(
        `Option ${
            question.options.length + 1
        }`
    );


    renderQuestions();
}


// =====================================================
// UPDATE OPTION
// =====================================================

function updateOption(
    questionIndex,
    optionIndex,
    value
) {

    const question =
        surveyData.questions[
            questionIndex
        ];


    if (!question) {
        return;
    }


    if (
        !Array.isArray(
            question.options
        )
    ) {

        question.options = [];
    }


    question.options[
        optionIndex
    ] = value;
}


// =====================================================
// DELETE OPTION
// =====================================================

function deleteOption(
    questionIndex,
    optionIndex
) {

    const question =
        surveyData.questions[
            questionIndex
        ];


    if (!question) {
        return;
    }


    if (
        !Array.isArray(
            question.options
        )
    ) {

        return;
    }


    // Keep at least one option
    if (
        question.options.length <= 1
    ) {

        showError(
            "At least one option is required."
        );

        return;
    }


    question.options.splice(
        optionIndex,
        1
    );


    renderQuestions();
}


// =====================================================
// SAVE / UPDATE SURVEY
// =====================================================

async function saveSurvey() {

    // IMPORTANT:
    // HTML IDs are title and description
    const titleInput =
        document.getElementById("title");


    const descriptionInput =
        document.getElementById("description");


    const title =
        titleInput
            ? titleInput.value.trim()
            : "";


    const description =
        descriptionInput
            ? descriptionInput.value.trim()
            : "";


    if (!title) {

        showError(
            "Please enter survey title."
        );

        return;
    }


    if (
        surveyData.questions.length === 0
    ) {

        showError(
            "Please add at least one question."
        );

        return;
    }


    // Validate questions
    for (
        let i = 0;
        i < surveyData.questions.length;
        i++
    ) {

        const question =
            surveyData.questions[i];


        if (
            !question.question ||
            !question.question.trim()
        ) {

            showError(
                `Please enter Question ${i + 1}.`
            );

            return;
        }


        // Validate options
        if (
            isOptionType(
                question.question_type
            )
        ) {

            if (
                !Array.isArray(
                    question.options
                ) ||
                question.options.length === 0
            ) {

                showError(
                    `Please add options for Question ${i + 1}.`
                );

                return;
            }


            for (
                let j = 0;
                j < question.options.length;
                j++
            ) {

                if (
                    !String(
                        question.options[j] || ""
                    ).trim()
                ) {

                    showError(
                        `Please fill Option ${j + 1} of Question ${i + 1}.`
                    );

                    return;
                }
            }
        }
    }


    const payload = {

        title:
            title,

        description:
            description,

        questions:
            surveyData.questions.map(
                function (question) {

                    return {

                        id:
                            question.id,

                        question:
                            question.question.trim(),

                        question_type:
                            normalizeQuestionType(
                                question.question_type
                            ),

                        options:
                            Array.isArray(
                                question.options
                            )
                                ? question.options.map(
                                    function (option) {
                                        return String(
                                            option
                                        ).trim();
                                    }
                                )
                                : [],

                        required:
                            Boolean(
                                question.required
                            )
                    };
                }
            )
    };


    const updateButton =
        document.getElementById(
            "updateButton"
        );


    try {

        if (updateButton) {

            updateButton.disabled =
                true;

            updateButton.innerText =
                "Updating...";
        }


        const response =
            await fetch(
                `/api/surveys/${surveyId}`,
                {

                    method: "PUT",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Unable to update survey."
            );
        }


        // Update local data
        surveyData.title =
            title;

        surveyData.description =
            description;


        showSuccess(
            "Survey updated successfully."
        );


        // Optional redirect
        setTimeout(
            function () {

                window.location.href =
                    "/surveys";

            },
            1000
        );


    } catch (error) {

        console.error(
            "Update survey error:",
            error
        );


        showError(
            error.message
        );


        if (updateButton) {

            updateButton.disabled =
                false;

            updateButton.innerText =
                "Update Survey";
        }
    }
}


// =====================================================
// PUBLISH SURVEY
// =====================================================

async function publishSurvey() {

    if (
        surveyData.questions.length === 0
    ) {

        showError(
            "Please add at least one question before publishing."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `/api/surveys/${surveyId}/publish`,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    }

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Unable to publish survey."
            );
        }


        showSuccess(
            "Survey published successfully."
        );


        setTimeout(
            function () {

                window.location.href =
                    "/surveys";

            },
            1000
        );


    } catch (error) {

        console.error(
            "Publish error:",
            error
        );


        showError(
            error.message
        );
    }
}


// =====================================================
// SHOW ERROR
// =====================================================

function showError(message) {

    const element =
        document.getElementById(
            "message"
        );


    if (!element) {

        alert(message);

        return;
    }


    element.className =
        "message error";


    element.innerText =
        message;


    element.style.display =
        "block";


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =====================================================
// SHOW SUCCESS
// =====================================================

function showSuccess(message) {

    const element =
        document.getElementById(
            "message"
        );


    if (!element) {

        alert(message);

        return;
    }


    element.className =
        "message success";


    element.innerText =
        message;


    element.style.display =
        "block";


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =====================================================
// HTML ESCAPE
// =====================================================

function escapeHtml(value) {

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}