#ifndef UTILS_H
#define UTILS_H

#include <Arduino.h>
#include <cstddef>
#include <memory>

#include <type_traits>
#include <utility>

byte ctob(const char *c);

int free_memory();

namespace std
{
    template <class T>
    struct _Unique_if
    {
        typedef unique_ptr<T> _Single_object;
    };

    template <class T>
    struct _Unique_if<T[]>
    {
        typedef unique_ptr<T[]> _Unknown_bound;
    };

    template <class T, size_t N>
    struct _Unique_if<T[N]>
    {
        typedef void _Known_bound;
    };

    template <class T, class... Args>
    typename _Unique_if<T>::_Single_object
    make_unique(Args &&...args)
    {
        return unique_ptr<T>(new T(std::forward<Args>(args)...));
    }

    template <class T>
    typename _Unique_if<T>::_Unknown_bound
    make_unique(size_t n)
    {
        typedef typename remove_extent<T>::type U;
        return unique_ptr<T>(new U[n]());
    }

    template <class T, class... Args>
    typename _Unique_if<T>::_Known_bound
    make_unique(Args &&...) = delete;

}

#endif