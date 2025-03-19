#ifndef UIBUILDER_HPP
#define UIBUILDER_HPP

#include <QLabel>
#include <QLayout>
#include "clickableqwidget.hpp"

class UiBuilder : public ClickableQWidget {
    Q_OBJECT
public:
    // return nullptr if parent does not have a layout
    static ClickableQWidget* build_import_page(QWidget* parent_with_layout);
    static ClickableQWidget* build_selection_page(QWidget* parent_with_layout);
    static ClickableQWidget* build_results_page(QWidget* parent_with_layout);
};

#endif // UIBUILDER_HPP
