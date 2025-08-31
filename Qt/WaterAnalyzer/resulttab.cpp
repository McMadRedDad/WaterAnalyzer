#include "resulttab.hpp"
#include "ui_resulttab.h"

ResultTab::ResultTab(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::ResultTab)
{
    ui->setupUi(this);
}

ResultTab::~ResultTab()
{
    delete ui;
}
