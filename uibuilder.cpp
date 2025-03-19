#include "uibuilder.hpp"

ClickableQWidget* UiBuilder::build_import_page(QWidget* parent_with_layout) {
    if (!parent_with_layout->layout()) {
        return nullptr;
    }

    QLabel*           capt = new QLabel();
    QVBoxLayout*      lyt = new QVBoxLayout();
    ClickableQWidget* w = new ClickableQWidget(parent_with_layout);

    capt->setText("Нажмите, чтобы открыть директорию со снимком.\nНазвание директории должно быть "
                  "оригинальным.");
    capt->setAlignment(Qt::AlignCenter);

    lyt->addWidget(capt);

    w->setLayout(lyt);

    return w;
}

ClickableQWidget* UiBuilder::build_selection_page(QWidget* parent_with_layout) {}

ClickableQWidget* UiBuilder::build_results_page(QWidget* parent_with_layout) {}
