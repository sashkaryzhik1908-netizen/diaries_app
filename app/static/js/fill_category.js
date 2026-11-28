// Данные ранее отправленной формы
const savedFormData = window.savedFormData || {};

// ==========================================
// MULTISELECT
// ==========================================
function addOption(variableName) {
    const select = document.getElementById("select_" + variableName);
    const list = document.getElementById("selected_" + variableName);
    const result = document.getElementById("result_" + variableName);
    const optionId = select.value;

    if (!optionId) return;

    const exists = Array.from(list.children).some(
        item => item.dataset.id === optionId
    );

    if (exists) return;

    const optionText = select.options[select.selectedIndex].text;
    const item = document.createElement("div");
    item.className = "list-group-item";
    item.dataset.id = optionId;

    const row = document.createElement("div");
    row.className = "d-flex justify-content-between align-items-center";

    const text = document.createElement("span");
    text.textContent = optionText;

    const buttons = document.createElement("div");

    const upButton = document.createElement("button");
    upButton.type = "button";
    upButton.className = "btn btn-sm btn-outline-secondary me-1";
    upButton.textContent = "↑";
    upButton.onclick = () => moveUp(item);

    const downButton = document.createElement("button");
    downButton.type = "button";
    downButton.className = "btn btn-sm btn-outline-secondary me-1";
    downButton.textContent = "↓";
    downButton.onclick = () => moveDown(item);

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "btn btn-sm btn-outline-danger";
    removeButton.textContent = "Удалить";
    removeButton.onclick = () => {
        item.remove();
        updateResult(list, result);
    };

    buttons.append(upButton, downButton, removeButton);
    row.append(text, buttons);
    item.appendChild(row);

    if (variableName === "drug") {
        const doseContainer = document.createElement("div");
        doseContainer.className = "d-flex align-items-center gap-2 mt-2";

        const doseInput = document.createElement("input");
        doseInput.type = "text";
        doseInput.className = "form-control w-50";
        doseInput.placeholder = "Введите дозировку";
        doseInput.name = `dose_${optionId}`;
        doseInput.value = getSavedDose(optionId);

        const doseHint = document.createElement("span");
        doseHint.className = "text-muted small text-nowrap";
        doseHint.textContent = "мкг/кг/мин";

        doseContainer.append(doseInput, doseHint);
        item.appendChild(doseContainer);
    }

    list.appendChild(item);
    updateResult(list, result);
}

function getSavedDose(optionId) {
    const saved = savedFormData[`dose_${optionId}`];
    return Array.isArray(saved) ? saved[0] || "" : saved || "";
}

function moveUp(item) {
    const previous = item.previousElementSibling;

    if (previous) {
        item.parentNode.insertBefore(item, previous);
    }

    const list = item.parentNode;
    const variableName = list.id.replace("selected_", "");
    const result = document.getElementById("result_" + variableName);

    updateResult(list, result);
}

function moveDown(item) {
    const next = item.nextElementSibling;

    if (next) {
        item.parentNode.insertBefore(next, item);
    }

    const list = item.parentNode;
    const variableName = list.id.replace("selected_", "");
    const result = document.getElementById("result_" + variableName);

    updateResult(list, result);
}

function updateResult(list, result) {
    const selectedIds = Array.from(list.children).map(
        item => item.dataset.id
    );

    result.value = selectedIds.join(",");
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('[id^="result_"]').forEach(result => {
        const variableName = result.id.replace("result_", "");
        const select = document.getElementById("select_" + variableName);
        const list = document.getElementById("selected_" + variableName);

        if (!select || !list || !result.value) return;

        const selectedIds = result.value.split(",");

        selectedIds.forEach(optionId => {
            const option = Array.from(select.options).find(
                item => item.value === optionId
            );

            if (option) {
                select.value = optionId;
                addOption(variableName);
            }
        });
    });
});

// ==========================================
// НАЗНАЧЕНИЯ
// ==========================================
document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("prescription-rows");
    const addButton = document.getElementById("add-prescription");

    if (!container || !addButton) return;

    const medicationsUrl = container.dataset.medicationsUrl;

    // Шаблон совместного препарата
    const additionalMedicationTemplate = document.getElementById(
        "additional-medication-template"
    );
    // Хранилище активных запросов препаратов по группам
    const medicationRequests = new WeakMap();

    function getSavedValue(name) {
        const saved = savedFormData[name];
        return Array.isArray(saved) ? saved[0] || "" : saved || "";
    }

    function getSavedList(name) {
        const saved = savedFormData[name];
        return Array.isArray(saved) ? saved : saved ? [saved] : [];
    }

    // Отображение полей терапии
    function toggleAntibacterialFields(group) {
        const purposeSelect = group.querySelector(".purpose-select");

        if (!purposeSelect) return;

        const selectedPurpose = (
            purposeSelect.selectedOptions[0]?.text || ""
        ).trim().toLowerCase();

        const isAntibacterial = selectedPurpose.includes("антибактериал");
        const isAnalgesic = selectedPurpose.includes("анальгетическ");

        // Изменение названия кнопки добавления препарата
        const addMedicationButton = group.querySelector(".add-medication");

        if (addMedicationButton) {
            addMedicationButton.textContent = isAntibacterial
                ? "Добавить антибактериальный препарат"
                : "Добавить препарат для совместного назначения";
        }

        // Индивидуальные поля антибактериальной терапии
        group.querySelectorAll(".antibacterial-fields").forEach(fields => {
            fields.classList.toggle("d-none", !isAntibacterial);

            fields.querySelectorAll("select, input").forEach(field => {
                field.disabled = !isAntibacterial;
            });
        });

        // Совместные препараты антибактериальной терапии
        group.querySelectorAll(".additional-medications-container").forEach(fields => {
            fields.classList.toggle("d-none", !isAntibacterial);

            fields.querySelectorAll("select, input, button").forEach(field => {
                field.disabled = !isAntibacterial;
            });
        });

        // Общие поля назначения
        group.querySelectorAll(".general-prescription-fields").forEach(fields => {
            const hideFields = isAntibacterial || isAnalgesic;

            fields.classList.toggle("d-none", hideFields);

            fields.querySelectorAll("select, input").forEach(field => {
                field.disabled = hideFields;
            });
        });

        // Доза и единица измерения
        group.querySelectorAll(".dose-field, .unit-field").forEach(fields => {
            fields.classList.toggle("d-none", isAnalgesic);

            fields.querySelectorAll("select, input").forEach(field => {
                field.disabled = isAnalgesic;

                if (isAnalgesic) {
                    field.removeAttribute("required");
                } else {
                    field.setAttribute("required", "");
                }
            });
        });
    }

    // Получение препаратов по цели терапии
    async function updateMedicationOptions(group, purposeId) {
        // Отмена предыдущего запроса для этой группы
        const previousController = medicationRequests.get(group);

        if (previousController) {
            previousController.abort();
        }

        const controller = new AbortController();
        medicationRequests.set(group, controller);

        // Получение актуальных полей выбора препаратов
        const getMedicationSelects = () => group.querySelectorAll(
            '.medication-row select[name^="medication_id"]'
        );

        getMedicationSelects().forEach(select => {
            select.innerHTML = '<option value="">Загрузка препаратов...</option>';
            select.disabled = true;
        });

        if (!purposeId) {
            getMedicationSelects().forEach(select => {
                select.innerHTML =
                    '<option value="">Сначала выберите цель терапии</option>';
                select.disabled = false;
            });

            medicationRequests.delete(group);
            return;
        }

        try {
            const url = medicationsUrl.replace(/0$/, purposeId);

            const response = await fetch(url, {
                signal: controller.signal
            });

            if (!response.ok) {
                throw new Error("Ошибка получения препаратов");
            }

            const medications = await response.json();

            // Игнорирование устаревшего ответа
            if (medicationRequests.get(group) !== controller) {
                return;
            }

            getMedicationSelects().forEach(select => {
                select.innerHTML = '<option value="">Выберите препарат</option>';

                medications.forEach(medication => {
                    const option = document.createElement("option");
                    option.value = medication.id;
                    option.textContent = medication.name;
                    select.appendChild(option);
                });

                select.disabled = false;
            });

        } catch (error) {
            // Игнорирование отменённых и устаревших запросов
            if (
                error.name === "AbortError" ||
                medicationRequests.get(group) !== controller
            ) {
                return;
            }

            console.error(error);

            getMedicationSelects().forEach(select => {
                select.innerHTML =
                    '<option value="">Ошибка загрузки препаратов</option>';
                select.disabled = false;
            });

        } finally {
            // Удаление завершённого запроса из хранилища
            if (medicationRequests.get(group) === controller) {
                medicationRequests.delete(group);
            }
        }
    }

    // Добавление совместного препарата
    function addAdditionalMedication(medicationRow) {
        const list = medicationRow.querySelector(
            ".additional-medications-list"
        );

        const mainMedicationSelect = medicationRow.querySelector(
            'select[name^="medication_id"]'
        );

        if (!list || !mainMedicationSelect || !additionalMedicationTemplate) {
            return;
        }

        if (mainMedicationSelect.disabled) return;

        const newMedication = additionalMedicationTemplate
            .content
            .firstElementChild
            .cloneNode(true);

        const medicationSelect = newMedication.querySelector(
            'select[name^="additional_medication_id"]'
        );

        // Копирование препаратов из общего справочника цели терапии
        medicationSelect.innerHTML = mainMedicationSelect.innerHTML;
        medicationSelect.selectedIndex = 0;

        list.appendChild(newMedication);
        return newMedication;
    }

    // Обновление названий полей
    function updateGroupNames(row, index) {
        row.dataset.groupIndex = index;

        row.querySelector('[name^="purpose_id"]').name =
            `purpose_id[${index}]`;

        row.querySelector('[name^="administration_method"]').name =
            `administration_method[${index}]`;

        row.querySelector('[name^="frequency"]').name =
            `frequency[${index}]`;

        row.querySelector('[name^="start_date"]').name =
            `start_date[${index}]`;

        row.querySelectorAll(".medication-row").forEach((medicationRow, medicationIndex) => {
            medicationRow.querySelector(
                'select[name^="medication_id"]'
            ).name = `medication_id[${index}][]`;

            medicationRow.querySelector(
                'select[name^="unit"]'
            ).name = `unit[${index}][]`;

            medicationRow.querySelector(
                'input[name^="dose"]'
            ).name = `dose[${index}][]`;

            medicationRow.querySelector(
                'select[name^="medication_method"]'
            ).name = `medication_method[${index}][]`;

            medicationRow.querySelector(
                'select[name^="medication_frequency"]'
            ).name = `medication_frequency[${index}][]`;

            medicationRow.querySelector(
                'input[name^="medication_start_date"]'
            ).name = `medication_start_date[${index}][]`;
            // Перенумерация совместных препаратов
            medicationRow.querySelectorAll(".additional-medication-row").forEach(additionalRow => {
                additionalRow.querySelector(
                    'select[name^="additional_medication_id"]'
                ).name = `additional_medication_id[${index}][${medicationIndex}][]`;

                additionalRow.querySelector(
                    'input[name^="additional_dose"]'
                ).name = `additional_dose[${index}][${medicationIndex}][]`;

                additionalRow.querySelector(
                    'select[name^="additional_unit"]'
                ).name = `additional_unit[${index}][${medicationIndex}][]`;
            });
        });
    }

    // Перенумерация назначений
    function reindexGroups() {
        container.querySelectorAll(".prescription-row").forEach(
            (row, index) => updateGroupNames(row, index)
        );
    }

    // Восстановление ранее сохранённых назначений
    async function restoreGroups() {
        const purposeKeys = Object.keys(savedFormData)
            .filter(key => /^purpose_id\[\d+\]$/.test(key))
            .sort((a, b) => Number(a.match(/\d+/)[0]) -
                Number(b.match(/\d+/)[0]));

        const firstRow = container.querySelector(".prescription-row");

        if (!firstRow) return;

        const templateRow = firstRow.cloneNode(true);

        if (!purposeKeys.length) {
            await updateMedicationOptions(firstRow, "");

            toggleAntibacterialFields(firstRow);

            reindexGroups();
            return;
        }

        container.innerHTML = "";

        for (const [groupPosition, key] of purposeKeys.entries()) {
            const oldIndex = key.match(/\d+/)[0];
            const row = templateRow.cloneNode(true);

            const purposeSelect = row.querySelector('[name^="purpose_id"]');
            const purposeId = getSavedValue(`purpose_id[${oldIndex}]`);

            purposeSelect.value = purposeId;

            row.querySelector('[name^="administration_method"]').value =
                getSavedValue(`administration_method[${oldIndex}]`);

            row.querySelector('[name^="frequency"]').value =
                getSavedValue(`frequency[${oldIndex}]`);

            row.querySelector('[name^="start_date"]').value =
                getSavedValue(`start_date[${oldIndex}]`);

            const medicationIds = getSavedList(
                `medication_id[${oldIndex}][]`
            );

            const doses = getSavedList(`dose[${oldIndex}][]`);
            const units = getSavedList(`unit[${oldIndex}][]`);

            const medicationMethods = getSavedList(
                `medication_method[${oldIndex}][]`
            );

            const medicationFrequencies = getSavedList(
                `medication_frequency[${oldIndex}][]`
            );

            const medicationStartDates = getSavedList(
                `medication_start_date[${oldIndex}][]`
            );

            const medicationsContainer = row.querySelector(
                ".medications-container"
            );

            // Загружаем препараты по выбранной цели
            await updateMedicationOptions(row, purposeId);

            const medicationTemplate = medicationsContainer
                .querySelector(".medication-row")
                .cloneNode(true);

            medicationsContainer.innerHTML = "";

            // Восстанавливаем ранее выбранные препараты
            medicationIds.forEach((medicationId, medicationIndex) => {
                const medicationRow = medicationTemplate.cloneNode(true);

                const medicationSelect = medicationRow.querySelector(
                    'select[name^="medication_id"]'
                );

                const unitSelect = medicationRow.querySelector(
                    'select[name^="unit"]'
                );

                const doseInput = medicationRow.querySelector(
                    'input[name^="dose"]'
                );

                const methodSelect = medicationRow.querySelector(
                    'select[name^="medication_method"]'
                );

                const frequencySelect = medicationRow.querySelector(
                    'select[name^="medication_frequency"]'
                );

                const startDateInput = medicationRow.querySelector(
                    'input[name^="medication_start_date"]'
                );

                medicationSelect.value = medicationId;
                unitSelect.value = units[medicationIndex] || "";
                doseInput.value = doses[medicationIndex] || "";

                if (methodSelect) {
                    methodSelect.value =
                        medicationMethods[medicationIndex] || "";
                }

                if (frequencySelect) {
                    frequencySelect.value =
                        medicationFrequencies[medicationIndex] || "";
                }

                if (startDateInput) {
                    startDateInput.value =
                        medicationStartDates[medicationIndex] || "";
                }
                    // Восстановление совместных препаратов
                    const additionalMedicationIds = getSavedList(
                        `additional_medication_id[${oldIndex}][${medicationIndex}][]`
                    );

                    const additionalDoses = getSavedList(
                        `additional_dose[${oldIndex}][${medicationIndex}][]`
                    );

                    const additionalUnits = getSavedList(
                        `additional_unit[${oldIndex}][${medicationIndex}][]`
                    );

                    additionalMedicationIds.forEach((additionalId, additionalIndex) => {
                        const additionalRow = addAdditionalMedication(medicationRow);

                        if (!additionalRow) return;

                        additionalRow.querySelector(
                            'select[name^="additional_medication_id"]'
                        ).value = additionalId;

                        additionalRow.querySelector(
                            'input[name^="additional_dose"]'
                        ).value = additionalDoses[additionalIndex] || "";

                        additionalRow.querySelector(
                            'select[name^="additional_unit"]'
                        ).value = additionalUnits[additionalIndex] || "";
                    });
                medicationsContainer.appendChild(medicationRow);
            });

            if (!medicationIds.length) {
                medicationsContainer.appendChild(
                    medicationTemplate.cloneNode(true)
                );
            }

            container.appendChild(row);

            updateGroupNames(row, groupPosition);
            toggleAntibacterialFields(row);
        }
    }

// Изменение цели терапии
container.addEventListener("change", function (event) {
    if (!event.target.matches(".purpose-select")) return;

    const group = event.target.closest(".prescription-row");
    const purposeId = event.target.value;

    // Удаление совместных препаратов
    group.querySelectorAll(".additional-medication-row").forEach(row => {
        row.remove();
    });

    // Удаление всех основных строк, кроме первой
    group.querySelectorAll(".medication-row").forEach((row, index) => {
        if (index > 0) {
            row.remove();
        }
    });

    // Очистка ранее введённых значений
    group.querySelectorAll("input").forEach(input => {
        input.value = "";
    });

    group.querySelectorAll("select").forEach(select => {
        if (!select.matches(".purpose-select")) {
            select.selectedIndex = 0;
        }
    });

    toggleAntibacterialFields(group);
    updateMedicationOptions(group, purposeId);

    reindexGroups();
});

    container.addEventListener("click", function (event) {
        const target = event.target;

        // Добавление совместного препарата к антибиотику
        const addAdditionalButton = target.closest(
            ".add-additional-medication"
        );

        if (addAdditionalButton) {
            const medicationRow = addAdditionalButton.closest(
                ".medication-row"
            );

            addAdditionalMedication(medicationRow);

            reindexGroups();

            return;
        }

// Удаление совместного препарата
        const removeAdditionalButton = target.closest(
            ".remove-additional-medication"
        );

        if (removeAdditionalButton) {
            const additionalRow = removeAdditionalButton.closest(
                ".additional-medication-row"
            );

            additionalRow.remove();

            reindexGroups();

            return;
        }
        // Добавление совместного препарата
        const addMedicationButton = target.closest(".add-medication");

        if (addMedicationButton) {
            const group = addMedicationButton.closest(".prescription-row");

            const medicationsContainer = group.querySelector(
                ".medications-container"
            );

            const firstMedication = medicationsContainer.querySelector(
                ".medication-row"
            );

            if (!firstMedication) return;

            const newMedication = firstMedication.cloneNode(true);

            // Очистка совместных препаратов в новой строке
            newMedication.querySelectorAll(".additional-medication-row").forEach(row => {
                row.remove();
            });

            newMedication.querySelectorAll("select").forEach(select => {
                select.selectedIndex = 0;
            });

            newMedication.querySelectorAll("input").forEach(input => {
                input.value = "";
            });

            medicationsContainer.appendChild(newMedication);

            toggleAntibacterialFields(group);
            reindexGroups();

            return;
        }

        // Удаление препарата
        const removeMedicationButton = target.closest(".remove-medication");

        if (removeMedicationButton) {
            const group = removeMedicationButton.closest(".prescription-row");
            const rows = group.querySelectorAll(".medication-row");

            if (rows.length > 1) {
                removeMedicationButton.closest(".medication-row").remove();
                reindexGroups();
            }

            return;
        }

        // Удаление назначения
        const removePrescriptionButton = target.closest(".remove-prescription");

        if (removePrescriptionButton) {
            const rows = container.querySelectorAll(".prescription-row");

            if (rows.length > 1) {
                removePrescriptionButton.closest(".prescription-row").remove();
                reindexGroups();
            }
        }
    });

    // Добавление нового назначения
    addButton.addEventListener("click", async function () {
        const firstRow = container.querySelector(".prescription-row");

        if (!firstRow) return;

        const newRow = firstRow.cloneNode(true);

        // Очистка совместных препаратов в новой группе
        newRow.querySelectorAll(".additional-medication-row").forEach(row => {
            row.remove();
        });

        newRow.querySelectorAll(".medication-row").forEach((row, index) => {
            if (index > 0) row.remove();
        });

        newRow.querySelectorAll("input").forEach(input => {
            input.value = "";
        });

        newRow.querySelectorAll("select").forEach(select => {
            select.selectedIndex = 0;
        });

        container.appendChild(newRow);

        toggleAntibacterialFields(newRow);

        await updateMedicationOptions(newRow, "");

        reindexGroups();
    });

    restoreGroups().then(reindexGroups);
});